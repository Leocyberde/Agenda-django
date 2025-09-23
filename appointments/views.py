from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, date
from .models import LinkAgendamento, Appointment
from salons.models import Salon, Service, Employee
from accounts.models import UserProfile
from .utils.scheduling import validate_appointment_request, compute_end_time, get_available_time_slots

def client_booking(request, token):
    """Página de agendamento do cliente via link único"""
    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        salon = link.salon

        # Se o link já está vinculado a um cliente, mostrar histórico e formulário de novo agendamento
        if link.client:
            client = link.client
            appointments = link.get_client_appointments()

            # Verificar se há reagendamentos pendentes
            pending_reschedules = appointments.filter(status='rescheduled')

            if request.method == 'POST':
                action = request.POST.get('action')

                if action == 'new_appointment':
                    # Criar novo agendamento
                    service_id = request.POST.get('service_id')
                    employee_id = request.POST.get('employee_id') or None
                    appointment_date = request.POST.get('appointment_date')
                    appointment_time = request.POST.get('appointment_time')
                    notes = request.POST.get('notes', '').strip()

                    # Validações básicas
                    if not all([service_id, appointment_date, appointment_time]):
                        messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                        return redirect('appointments:client_booking', token=token)

                    try:
                        with transaction.atomic():
                            service = Service.objects.get(id=service_id, salon=salon, is_active=True)

                            # Preparar funcionário se especificado
                            employee = None
                            if employee_id:
                                employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)

                            # Verificar data/hora
                            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                            appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()

                            # Calcular horários de início e fim
                            start_dt = datetime.combine(appointment_date_obj, appointment_time_obj)
                            start_dt = timezone.make_aware(start_dt)
                            end_dt = compute_end_time(appointment_date_obj, appointment_time_obj, service)
                            end_dt = timezone.make_aware(end_dt)

                            # Validar agendamento usando lógica centralizada com proteção contra race conditions
                            is_valid, error_msg, assigned_employee = validate_appointment_request(
                                salon=salon,
                                service=service,
                                client=client,
                                start_dt=start_dt,
                                end_dt=end_dt,
                                employee=employee,
                                use_locking=True
                            )

                            if not is_valid:
                                messages.error(request, error_msg)
                                return redirect('appointments:client_booking', token=token)

                            # Criar agendamento
                            appointment = Appointment.objects.create(
                                client=client,
                                salon=salon,
                                service=service,
                                employee=assigned_employee,
                                appointment_date=appointment_date_obj,
                                appointment_time=appointment_time_obj,
                                notes=notes,
                                status='scheduled'
                            )

                            messages.success(request, 'Agendamento realizado com sucesso!')
                            return redirect('appointments:client_booking', token=token)

                    except Exception as e:
                        messages.error(request, f'Erro ao criar agendamento: {str(e)}')
                        return redirect('appointments:client_booking', token=token)

            # Mostrar histórico e formulário
            services = salon.services.filter(is_active=True)
            employees = salon.employees.filter(is_active=True)

            return render(request, 'appointments/client_booking.html', {
                'link': link,
                'salon': salon,
                'client': client,
                'appointments': appointments,
                'pending_reschedules': pending_reschedules,
                'services': services,
                'employees': employees,
                'is_existing_client': True,
                'today': timezone.now().date()
            })

        else:
            # Link não vinculado - formulário de primeiro agendamento
            if request.method == 'POST':
                try:
                    with transaction.atomic():
                        # Dados do cliente
                        client_name = request.POST.get('client_name', '').strip()
                        client_email = request.POST.get('client_email', '').strip()
                        client_phone = request.POST.get('client_phone', '').strip()

                        # Dados do agendamento
                        service_id = request.POST.get('service_id')
                        employee_id = request.POST.get('employee_id') or None
                        appointment_date = request.POST.get('appointment_date')
                        appointment_time = request.POST.get('appointment_time')
                        notes = request.POST.get('notes', '').strip()

                        # Validações
                        if not all([client_name, client_email, service_id, appointment_date, appointment_time]):
                            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
                            return redirect('appointments:client_booking', token=token)

                        # Verificar se já existe usuário com este email
                        existing_user = User.objects.filter(email=client_email).first()
                        if existing_user:
                            # Se já existe, usar o usuário existente
                            client = existing_user
                        else:
                            # Criar novo usuário
                            client = User.objects.create_user(
                                username=client_email,
                                email=client_email,
                                first_name=client_name.split()[0] if client_name.split() else client_name,
                                last_name=' '.join(client_name.split()[1:]) if len(client_name.split()) > 1 else ''
                            )

                        # Criar ou atualizar perfil
                        profile, created = UserProfile.objects.get_or_create(user=client)
                        if client_phone:
                            profile.phone = client_phone
                        profile.user_type = 'client'
                        profile.save()

                        # Vincular cliente ao link
                        link.client = client
                        link.save()

                        # Criar agendamento
                        service = Service.objects.get(id=service_id, salon=salon, is_active=True)

                        # Preparar funcionário se especificado
                        employee = None
                        if employee_id:
                            employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)

                        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                        appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()

                        # Calcular horários de início e fim
                        start_dt = datetime.combine(appointment_date_obj, appointment_time_obj)
                        start_dt = timezone.make_aware(start_dt)
                        end_dt = compute_end_time(appointment_date_obj, appointment_time_obj, service)
                        end_dt = timezone.make_aware(end_dt)

                        # Validar agendamento usando lógica centralizada
                        is_valid, error_msg, assigned_employee = validate_appointment_request(
                            salon=salon,
                            service=service,
                            client=client,
                            start_dt=start_dt,
                            end_dt=end_dt,
                            employee=employee
                        )

                        if not is_valid:
                            messages.error(request, error_msg)
                            return redirect('appointments:client_booking', token=token)

                        appointment = Appointment.objects.create(
                            client=client,
                            salon=salon,
                            service=service,
                            employee=assigned_employee,
                            appointment_date=appointment_date_obj,
                            appointment_time=appointment_time_obj,
                            notes=notes,
                            status='scheduled'
                        )

                        messages.success(request, 'Cadastro e agendamento realizados com sucesso!')
                        return redirect('appointments:client_booking', token=token)

                except Exception as e:
                    messages.error(request, f'Erro ao processar: {str(e)}')
                    return redirect('appointments:client_booking', token=token)

            # Formulário inicial para cliente não vinculado
            services = salon.services.filter(is_active=True)
            employees = salon.employees.filter(is_active=True)

            return render(request, 'appointments/client_booking.html', {
                'link': link,
                'salon': salon,
                'services': services,
                'employees': employees,
                'is_existing_client': False,
                'today': timezone.now().date()
            })

    except LinkAgendamento.DoesNotExist:
        return render(request, 'appointments/invalid_link.html')

@login_required
def confirm_reschedule(request, token, appointment_id):
    """Cliente confirma o reagendamento proposto"""
    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        appointment = get_object_or_404(Appointment, 
                                      id=appointment_id, 
                                      client=link.client,
                                      salon=link.salon,
                                      status='rescheduled')

        # Confirmar reagendamento
        appointment.appointment_date = appointment.rescheduled_date
        appointment.appointment_time = appointment.rescheduled_time
        appointment.rescheduled_date = None
        appointment.rescheduled_time = None
        appointment.rescheduled_reason = ''
        appointment.status = 'confirmed'
        appointment.save()

        messages.success(request, 'Reagendamento confirmado com sucesso!')

    except Exception as e:
        messages.error(request, f'Erro ao confirmar reagendamento: {str(e)}')

    return redirect('appointments:client_booking', token=token)

@login_required
def reject_reschedule(request, token, appointment_id):
    """Cliente rejeita o reagendamento proposto"""
    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        appointment = get_object_or_404(Appointment, 
                                      id=appointment_id, 
                                      client=link.client,
                                      salon=link.salon,
                                      status='rescheduled')

        # Cancelar agendamento
        appointment.status = 'cancelled'
        appointment.rescheduled_date = None
        appointment.rescheduled_time = None
        appointment.rescheduled_reason = ''
        appointment.save()

        messages.success(request, 'Reagendamento rejeitado. Agendamento foi cancelado.')

    except Exception as e:
        messages.error(request, f'Erro ao rejeitar reagendamento: {str(e)}')

    return redirect('appointments:client_booking', token=token)

def get_available_slots(request, token):
    """API para retornar horários disponíveis via AJAX"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Método não permitido'}, status=405)

    try:
        link = get_object_or_404(LinkAgendamento, token=token, is_active=True)
        salon = link.salon

        # Parâmetros da requisição
        service_id = request.GET.get('service_id')
        employee_id = request.GET.get('employee_id') or None
        date_str = request.GET.get('date')

        if not service_id or not date_str:
            return JsonResponse({'error': 'Parâmetros obrigatórios: service_id e date'}, status=400)

        try:
            service = Service.objects.get(id=service_id, salon=salon, is_active=True)
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Verificar se a data não é no passado
            if appointment_date < timezone.now().date():
                return JsonResponse({'slots': []})

            # Buscar funcionário se especificado
            employee = None
            if employee_id:
                try:
                    employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)
                except Employee.DoesNotExist:
                    return JsonResponse({'error': 'Funcionário não encontrado'}, status=400)

            # Buscar horários disponíveis
            available_slots = get_available_time_slots(salon, service, appointment_date, employee)

            return JsonResponse({'slots': available_slots})

        except Service.DoesNotExist:
            return JsonResponse({'error': 'Serviço não encontrado'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Formato de data inválido'}, status=400)

    except LinkAgendamento.DoesNotExist:
        return JsonResponse({'error': 'Link não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)