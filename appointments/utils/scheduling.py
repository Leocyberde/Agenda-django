"""
Módulo central para lógica de agendamentos e validação de conflitos.
Centraliza todas as regras de negócio relacionadas a agendamentos.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import models
from typing import Tuple, Optional


def compute_end_time(start_date, start_time, service):
    """Calcula o horário de término baseado na duração do serviço"""
    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = start_datetime + timedelta(minutes=service.duration)
    return end_datetime


def compute_end_time_aware(start_dt, service):
    """Calcula o horário de término timezone-aware baseado na duração do serviço"""
    return start_dt + timedelta(minutes=service.duration)


def overlaps(a_start, a_end, b_start, b_end):
    """Verifica se dois intervalos de tempo se sobrepõem"""
    return a_start < b_end and b_start < a_end


def is_within_salon_hours(salon, start_dt, end_dt):
    """Verifica se o agendamento está completamente dentro do horário de funcionamento"""
    day_of_week = start_dt.weekday()
    open_time, close_time = salon.get_working_hours(day_of_week)
    
    if not open_time or not close_time:
        return False, "Salão não funciona neste dia da semana"
    
    # Converter para timezone-aware usando o mesmo timezone do start_dt
    salon_open = timezone.make_aware(
        datetime.combine(start_dt.date(), open_time),
        timezone=start_dt.tzinfo
    )
    salon_close = timezone.make_aware(
        datetime.combine(start_dt.date(), close_time),
        timezone=start_dt.tzinfo
    )
    
    if start_dt < salon_open:
        return False, f"Salão abre às {open_time.strftime('%H:%M')}"
    
    if end_dt > salon_close:
        return False, f"Agendamento ultrapassa o horário de fechamento ({close_time.strftime('%H:%M')})"
    
    return True, ""


def is_salon_open(salon, start_dt, end_dt):
    """Verifica se o salão está aberto no momento do agendamento"""
    # Verificar se está temporariamente fechado
    if salon.is_temporarily_closed:
        if salon.closed_until:
            if start_dt < salon.closed_until:
                if salon.closure_note:
                    return False, f"Salão temporariamente fechado: {salon.closure_note}"
                else:
                    return False, f"Salão fechado até {salon.closed_until.strftime('%d/%m/%Y %H:%M')}"
        else:
            if salon.closure_note:
                return False, f"Salão temporariamente fechado: {salon.closure_note}"
            else:
                return False, "Salão temporariamente fechado"
    
    # Verificar horário de funcionamento
    return is_within_salon_hours(salon, start_dt, end_dt)


def employee_can_perform_service(employee, service):
    """Verifica se o funcionário pode realizar o serviço"""
    if not employee or not employee.is_active:
        return False, "Funcionário não está ativo"
    
    if not employee.services.filter(id=service.id).exists():
        return False, "Funcionário não está qualificado para este serviço"
    
    return True, ""


def is_employee_available(employee, start_dt, end_dt, use_locking=False):
    """Verifica se o funcionário está disponível no horário solicitado"""
    if not employee:
        return True, ""
    
    from appointments.models import Appointment
    
    # Buscar agendamentos conflitantes do funcionário
    query = Appointment.objects.filter(
        employee=employee,
        appointment_date=start_dt.date(),
        status__in=['scheduled', 'confirmed']
    )
    
    # Usar select_for_update para prevenir race conditions se solicitado
    if use_locking:
        query = query.select_for_update()
    
    conflicting_appointments = query
    
    for appointment in conflicting_appointments:
        # Criar datetime timezone-aware para comparação
        existing_start = timezone.make_aware(
            datetime.combine(appointment.appointment_date, appointment.appointment_time),
            timezone=start_dt.tzinfo
        )
        existing_end = existing_start + timedelta(minutes=appointment.service.duration)
        
        if overlaps(start_dt, end_dt, existing_start, existing_end):
            return False, f"Funcionário já tem agendamento às {appointment.appointment_time.strftime('%H:%M')}"
    
    return True, ""


def client_has_conflict(client, salon, start_dt, end_dt, exclude_appointment=None, use_locking=False):
    """Verifica se o cliente já tem agendamento conflitante"""
    from appointments.models import Appointment
    
    query = Appointment.objects.filter(
        client=client,
        salon=salon,
        appointment_date=start_dt.date(),
        status__in=['scheduled', 'confirmed']
    )
    
    if exclude_appointment:
        query = query.exclude(id=exclude_appointment.id)
    
    # Usar select_for_update para prevenir race conditions se solicitado
    if use_locking:
        query = query.select_for_update()
    
    for appointment in query:
        # Criar datetime timezone-aware para comparação
        existing_start = timezone.make_aware(
            datetime.combine(appointment.appointment_date, appointment.appointment_time),
            timezone=start_dt.tzinfo
        )
        existing_end = existing_start + timedelta(minutes=appointment.service.duration)
        
        if overlaps(start_dt, end_dt, existing_start, existing_end):
            return True, f"Cliente já tem agendamento às {appointment.appointment_time.strftime('%H:%M')}"
    
    return False, ""


def find_available_employee(salon, service, start_dt, end_dt):
    """Encontra um funcionário disponível para o serviço no horário especificado"""
    from salons.models import Employee
    
    # Buscar funcionários qualificados
    qualified_employees = Employee.objects.filter(
        salon=salon,
        is_active=True,
        services=service
    ).distinct()
    
    for employee in qualified_employees:
        can_perform, _ = employee_can_perform_service(employee, service)
        if not can_perform:
            continue
            
        is_available, _ = is_employee_available(employee, start_dt, end_dt)
        if is_available:
            return employee
    
    return None


def validate_appointment_request(salon, service, client, start_dt, end_dt, employee=None, exclude_appointment=None, use_locking=False):
    """
    Valida um pedido de agendamento considerando todas as regras de negócio.
    Com proteção contra race conditions quando use_locking=True.
    
    Returns:
        Tuple[bool, str, Optional[Employee]]: (sucesso, mensagem_erro, funcionario_atribuido)
    """
    # 1. Verificar se é no futuro
    if start_dt <= timezone.now():
        return False, "Não é possível agendar para horários passados", None
    
    # 2. Verificar se o salão está aberto
    salon_open, error_msg = is_salon_open(salon, start_dt, end_dt)
    if not salon_open:
        return False, error_msg, None
    
    # 3. Verificar se o serviço está ativo
    if not service.is_active:
        return False, "Este serviço não está mais disponível", None
    
    # 4. Se funcionário foi especificado, validar
    if employee:
        can_perform, error_msg = employee_can_perform_service(employee, service)
        if not can_perform:
            return False, error_msg, None
        
        is_available, error_msg = is_employee_available(employee, start_dt, end_dt, use_locking)
        if not is_available:
            return False, error_msg, None
    else:
        # 5. Encontrar funcionário disponível
        employee = find_available_employee(salon, service, start_dt, end_dt)
        if not employee:
            return False, "Nenhum funcionário disponível para este horário e serviço", None
        
        # Re-verificar disponibilidade com locking se solicitado
        if use_locking:
            is_available, error_msg = is_employee_available(employee, start_dt, end_dt, use_locking)
            if not is_available:
                return False, error_msg, None
    
    # 6. Verificar conflito com cliente
    has_conflict, error_msg = client_has_conflict(client, salon, start_dt, end_dt, exclude_appointment, use_locking)
    if has_conflict:
        return False, error_msg, None
    
    # 7. Verificar se o horário específico já está ocupado no salão
    from appointments.models import Appointment
    
    existing_query = Appointment.objects.filter(
        salon=salon,
        appointment_date=start_dt.date(),
        appointment_time=start_dt.time(),
        status__in=['scheduled', 'confirmed']
    )
    
    if exclude_appointment:
        existing_query = existing_query.exclude(id=exclude_appointment.id)
    
    if employee:
        # Se tem funcionário específico, verificar se ele está livre neste horário exato
        existing_query = existing_query.filter(employee=employee)
    
    # Aplicar locking se solicitado
    if use_locking:
        existing_query = existing_query.select_for_update()
    
    if existing_query.exists():
        return False, "Este horário já está ocupado", None
    
    return True, "", employee


def get_available_time_slots(salon, service, date, employee=None):
    """
    Retorna horários disponíveis para agendamento em uma data específica.
    
    Args:
        salon: Instância do salão
        service: Instância do serviço
        date: Data para verificar disponibilidade
        employee: Funcionário específico (opcional)
    
    Returns:
        List[str]: Lista de horários disponíveis em formato "HH:MM"
    """
    from appointments.models import Appointment
    
    available_slots = []
    
    # Verificar se o salão funciona neste dia
    day_of_week = date.weekday()
    open_time, close_time = salon.get_working_hours(day_of_week)
    
    if not open_time or not close_time:
        return available_slots
    
    # Gerar slots de 30 em 30 minutos
    current_time = datetime.combine(date, open_time)
    end_time = datetime.combine(date, close_time)
    
    while current_time < end_time:
        slot_start = current_time
        slot_end = compute_end_time(date, current_time.time(), service)
        
        # Verificar se o slot termina antes do fechamento
        if slot_end <= end_time:
            # Validar se este horário está disponível
            is_valid, _, _ = validate_appointment_request(
                salon=salon,
                service=service,
                client=None,  # Não verificar conflito de cliente nesta função
                start_dt=slot_start,
                end_dt=slot_end,
                employee=employee
            )
            
            if is_valid:
                available_slots.append(current_time.strftime('%H:%M'))
        
        # Próximo slot (incrementar 30 minutos)
        current_time += timedelta(minutes=30)
    
    return available_slots