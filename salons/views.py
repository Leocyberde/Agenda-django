from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import transaction
import uuid
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse
from subscriptions.views import subscription_required
from .models import Salon, Service, Employee, BookingToken
from .forms import SalonForm, ServiceForm, EmployeeForm, EmployeeEditForm
from appointments.models import Appointment

@login_required
def create_salon(request):
    """Criar salão para proprietário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')

    # Verificar se já tem salão
    if hasattr(request.user, 'salon'):
        return redirect('salons:owner_dashboard')

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES)
        if form.is_valid():
            salon = form.save(commit=False)
            salon.owner = request.user
            salon.save()
            messages.success(request, 'Salão criado com sucesso!')
            return redirect('salons:owner_dashboard')
    else:
        form = SalonForm()

    return render(request, 'salons/create_salon.html', {'form': form})

@subscription_required
def owner_dashboard(request):
    """Dashboard do proprietário"""
    salon = request.user.salon

    # Estatísticas
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    stats = {
        'appointments_today': Appointment.objects.filter(
            salon=salon, 
            appointment_date=today
        ).count(),
        'appointments_week': Appointment.objects.filter(
            salon=salon,
            appointment_date__gte=week_start,
            appointment_date__lte=today
        ).count(),
        'pending_appointments': Appointment.objects.filter(
            salon=salon,
            status='scheduled'
        ).count(),
        'total_services': salon.services.filter(is_active=True).count(),
        'total_employees': salon.employees.filter(is_active=True).count(),
    }

    # Próximos agendamentos
    upcoming_appointments = Appointment.objects.filter(
        salon=salon,
        appointment_date__gte=today,
        status__in=['scheduled', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:5]

    # Informações da assinatura
    subscription = request.user.subscription

    return render(request, 'salons/owner_dashboard.html', {
        'salon': salon,
        'stats': stats,
        'upcoming_appointments': upcoming_appointments,
        'subscription': subscription
    })

@subscription_required
def edit_salon(request):
    """Editar informações do salão"""
    salon = request.user.salon

    if request.method == 'POST':
        form = SalonForm(request.POST, request.FILES, instance=salon)
        if form.is_valid():
            form.save()
            messages.success(request, 'Salão atualizado com sucesso!')
            return redirect('salons:owner_dashboard')
    else:
        form = SalonForm(instance=salon)

    return render(request, 'salons/edit_salon.html', {
        'form': form,
        'salon': salon
    })

@subscription_required
def services_list(request):
    """Lista de serviços do salão"""
    salon = request.user.salon
    services = salon.services.all().order_by('name')

    return render(request, 'salons/services_list.html', {
        'services': services,
        'salon': salon
    })

@subscription_required
def create_service(request):
    """Criar novo serviço"""
    salon = request.user.salon

    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.salon = salon
            service.save()
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('salons:services_list')
    else:
        form = ServiceForm()

    return render(request, 'salons/create_service.html', {
        'form': form,
        'salon': salon
    })

@subscription_required
def edit_service(request, service_id):
    """Editar serviço"""
    salon = request.user.salon
    service = get_object_or_404(Service, id=service_id, salon=salon)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso!')
            return redirect('salons:services_list')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'salons/edit_service.html', {
        'form': form,
        'service': service,
        'salon': salon
    })

@subscription_required
def delete_service(request, service_id):
    """Deletar serviço"""
    salon = request.user.salon
    service = get_object_or_404(Service, id=service_id, salon=salon)

    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Serviço deletado com sucesso!')
        return redirect('salons:services_list')

    return render(request, 'salons/delete_service.html', {
        'service': service,
        'salon': salon
    })

@subscription_required
def appointments_list(request):
    """Lista de agendamentos do salão"""
    salon = request.user.salon

    # Filtros
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    appointments = Appointment.objects.filter(salon=salon)

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date=filter_date)
        except ValueError:
            pass

    appointments = appointments.order_by('-appointment_date', '-appointment_time')

    return render(request, 'salons/appointments_list.html', {
        'appointments': appointments,
        'salon': salon,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Appointment.STATUS_CHOICES
    })

# ============== GERENCIAMENTO DE FUNCIONÁRIOS ==============

@subscription_required
def employees_list(request):
    """Lista de funcionários do salão"""
    salon = request.user.salon
    employees = salon.employees.all().order_by('user__first_name')

    return render(request, 'salons/employees_list.html', {
        'employees': employees,
        'salon': salon
    })

@subscription_required
@transaction.atomic
def create_employee(request):
    """Criar novo funcionário"""
    salon = request.user.salon

    if request.method == 'POST':
        form = EmployeeForm(request.POST, salon=salon)
        if form.is_valid():
            try:
                # Criar usuário
                user = User.objects.create_user(
                    username=form.cleaned_data['email'],
                    email=form.cleaned_data['email'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    password=form.cleaned_data['password']
                )

                # Definir como funcionário
                user.profile.user_type = 'employee'
                user.profile.save()

                # Criar employee
                employee = form.save(commit=False)
                employee.user = user
                employee.salon = salon
                employee.save()
                form.save_m2m()  # Salvar many-to-many relationships

                messages.success(request, f'Funcionário {user.get_full_name()} criado com sucesso!')
                return redirect('salons:employees_list')
            except Exception as e:
                messages.error(request, f'Erro ao criar funcionário: {str(e)}')
    else:
        form = EmployeeForm(salon=salon)

    return render(request, 'salons/create_employee.html', {
        'form': form,
        'salon': salon
    })

@subscription_required
def edit_employee(request, employee_id):
    """Editar funcionário"""
    salon = request.user.salon
    employee = get_object_or_404(Employee, id=employee_id, salon=salon)

    if request.method == 'POST':
        form = EmployeeEditForm(request.POST, instance=employee, salon=salon)
        if form.is_valid():
            form.save()
            messages.success(request, f'Funcionário {employee.user.get_full_name()} atualizado com sucesso!')
            return redirect('salons:employees_list')
    else:
        form = EmployeeEditForm(instance=employee, salon=salon)

    return render(request, 'salons/edit_employee.html', {
        'form': form,
        'employee': employee,
        'salon': salon
    })

@subscription_required
def delete_employee(request, employee_id):
    """Deletar funcionário"""
    salon = request.user.salon
    employee = get_object_or_404(Employee, id=employee_id, salon=salon)

    if request.method == 'POST':
        user = employee.user
        employee_name = user.get_full_name()

        # Deletar funcionário (o usuário também será deletado devido ao CASCADE)
        employee.delete()
        user.delete()

        messages.success(request, f'Funcionário {employee_name} removido com sucesso!')
        return redirect('salons:employees_list')

    return render(request, 'salons/delete_employee.html', {
        'employee': employee,
        'salon': salon
    })

# ============== PAINEL DO FUNCIONÁRIO ==============

def is_employee(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.user_type == 'employee'

@login_required
def employee_dashboard(request):
    """Dashboard do funcionário"""
    if not (hasattr(request.user, 'profile') and request.user.profile.user_type == 'employee'):
        messages.error(request, 'Acesso negado. Você precisa ser um funcionário para acessar esta área.')
        return redirect('accounts:dashboard')
    """Dashboard do funcionário"""
    employee = request.user.employee_profile
    salon = employee.salon

    # Estatísticas do funcionário
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    my_appointments = Appointment.objects.filter(
        employee=employee,
        appointment_date__gte=today
    ).order_by('appointment_date', 'appointment_time')

    stats = {
        'appointments_today': my_appointments.filter(
            appointment_date=today
        ).count(),
        'appointments_week': my_appointments.filter(
            appointment_date__gte=week_start,
            appointment_date__lte=today
        ).count(),
        'pending_appointments': my_appointments.filter(
            status='scheduled'
        ).count(),
        'my_services': employee.services.filter(is_active=True).count(),
    }

    # Próximos agendamentos do funcionário
    upcoming_appointments = my_appointments.filter(
        status__in=['scheduled', 'confirmed']
    )[:5]

    return render(request, 'salons/employee_dashboard.html', {
        'employee': employee,
        'salon': salon,
        'stats': stats,
        'upcoming_appointments': upcoming_appointments
    })

@login_required
def employee_appointments(request):
    """Lista de agendamentos do funcionário"""
    if not (hasattr(request.user, 'profile') and request.user.profile.user_type == 'employee'):
        messages.error(request, 'Acesso negado. Você precisa ser um funcionário para acessar esta área.')
        return redirect('accounts:dashboard')
    """Lista de agendamentos do funcionário"""
    employee = request.user.employee_profile
    salon = employee.salon

    # Filtros
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    appointments = Appointment.objects.filter(employee=employee)

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_date=filter_date)
        except ValueError:
            pass

    appointments = appointments.order_by('-appointment_date', '-appointment_time')

    return render(request, 'salons/employee_appointments.html', {
        'appointments': appointments,
        'employee': employee,
        'salon': salon,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Appointment.STATUS_CHOICES
    })

# ============== LINK DE AGENDAMENTO ==============

@subscription_required
def generate_booking_link(request):
    """Gerar ou regenerar link de agendamento"""
    salon = request.user.salon

    if request.method == 'POST':
        # Criar ou atualizar token de agendamento
        booking_token, created = BookingToken.objects.get_or_create(
            salon=salon,
            defaults={'is_active': True}
        )

        if not created:
            # Regenerar token
            booking_token.token = ''
            booking_token.is_active = True
            booking_token.save()

        messages.success(request, 'Link de agendamento gerado com sucesso!')
        return redirect('salons:generate_booking_link')

    # Obter token existente
    try:
        booking_token = salon.booking_token
    except BookingToken.DoesNotExist:
        booking_token = None

    return render(request, 'salons/generate_booking_link.html', {
        'salon': salon,
        'booking_token': booking_token
    })

@subscription_required
def toggle_booking_link(request):
    """Ativar/desativar link de agendamento"""
    salon = request.user.salon

    try:
        booking_token = salon.booking_token
        booking_token.is_active = not booking_token.is_active
        booking_token.save()

        status = "ativado" if booking_token.is_active else "desativado"
        messages.success(request, f'Link de agendamento {status} com sucesso!')
    except BookingToken.DoesNotExist:
        messages.error(request, 'Nenhum link de agendamento encontrado. Gere um novo link primeiro.')

    return redirect('salons:owner_dashboard')

# ============== AGENDAMENTO PÚBLICO ==============

def public_booking(request, token):
    """Página pública de agendamento via token"""
    try:
        booking_token = get_object_or_404(BookingToken, token=token, is_active=True)
        salon = booking_token.salon
        services = salon.services.filter(is_active=True)
        employees = salon.employees.filter(is_active=True)

        if request.method == 'POST':
            try:
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
                    return render(request, 'salons/public_booking.html', {
                        'salon': salon, 'services': services, 'employees': employees, 'token': token
                    })

                # Verificar se o serviço existe e pertence ao salão
                try:
                    service = Service.objects.get(id=service_id, salon=salon, is_active=True)
                except Service.DoesNotExist:
                    messages.error(request, 'Serviço inválido.')
                    return render(request, 'salons/public_booking.html', {
                        'salon': salon, 'services': services, 'employees': employees, 'token': token
                    })

                # Verificar/atribuir funcionário
                employee = None
                if employee_id and employee_id != "":
                    # Funcionário específico foi selecionado
                    try:
                        employee = Employee.objects.get(id=employee_id, salon=salon, is_active=True)
                        # Verificar se o funcionário pode fazer o serviço
                        if not employee.services.filter(id=service_id).exists():
                            messages.error(request, 'Este profissional não realiza o serviço selecionado.')
                            return render(request, 'salons/public_booking.html', {
                                'salon': salon, 'services': services, 'employees': employees, 'token': token
                            })
                    except Employee.DoesNotExist:
                        messages.error(request, 'Profissional inválido.')
                        return render(request, 'salons/public_booking.html', {
                            'salon': salon, 'services': services, 'employees': employees, 'token': token
                        })
                else:
                    # Nenhum funcionário específico - atribuir automaticamente um disponível que possa fazer o serviço
                    available_employees = salon.employees.filter(
                        is_active=True,
                        services=service  # Funcionários que podem fazer este serviço
                    ).distinct()

                    if available_employees.exists():
                        # Selecionar o primeiro funcionário disponível que pode fazer o serviço
                        employee = available_employees.first()
                    else:
                        # Nenhum funcionário pode fazer este serviço
                        messages.error(request, 'Nenhum profissional disponível para este serviço no momento. Tente novamente mais tarde ou escolha outro serviço.')
                        return render(request, 'salons/public_booking.html', {
                            'salon': salon, 'services': services, 'employees': employees, 'token': token
                        })

                # Verificar data e horário
                from datetime import datetime, date
                try:
                    appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
                    appointment_time_obj = datetime.strptime(appointment_time, '%H:%M').time()
                except ValueError:
                    messages.error(request, 'Data ou horário inválido.')
                    return render(request, 'salons/public_booking.html', {
                        'salon': salon, 'services': services, 'employees': employees, 'token': token
                    })

                # Verificar se a data não é no passado
                if appointment_date_obj < date.today():
                    messages.error(request, 'Não é possível agendar para datas passadas.')
                    return render(request, 'salons/public_booking.html', {
                        'salon': salon, 'services': services, 'employees': employees, 'token': token
                    })

                # Verificar se já existe agendamento no mesmo horário
                existing_appointment = None
                if employee:
                    existing_appointment = Appointment.objects.filter(
                        salon=salon,
                        employee=employee,
                        appointment_date=appointment_date_obj,
                        appointment_time=appointment_time_obj
                    ).first()
                else:
                    existing_appointment = Appointment.objects.filter(
                        salon=salon,
                        appointment_date=appointment_date_obj,
                        appointment_time=appointment_time_obj
                    ).first()

                if existing_appointment:
                    messages.error(request, 'Este horário já está ocupado. Escolha outro horário.')
                    return render(request, 'salons/public_booking.html', {
                        'salon': salon, 'services': services, 'employees': employees, 'token': token
                    })

                # Criar ou obter o usuário cliente
                with transaction.atomic():
                    # Verificar se já existe um usuário com este email
                    try:
                        client = User.objects.get(email=client_email)
                        # Atualizar nome se necessário
                        if not client.first_name or not client.last_name:
                            names = client_name.split(' ', 1)
                            client.first_name = names[0]
                            client.last_name = names[1] if len(names) > 1 else ''
                            client.save()
                    except User.DoesNotExist:
                        # Criar novo cliente
                        names = client_name.split(' ', 1)
                        client = User.objects.create_user(
                            username=client_email,
                            email=client_email,
                            first_name=names[0],
                            last_name=names[1] if len(names) > 1 else ''
                        )
                        # Definir como cliente
                        client.profile.user_type = 'client'
                        if client_phone:
                            client.profile.phone = client_phone
                        client.profile.save()

                    # Criar o agendamento
                    appointment = Appointment.objects.create(
                        client=client,
                        salon=salon,
                        service=service,
                        employee=employee,
                        appointment_date=appointment_date_obj,
                        appointment_time=appointment_time_obj,
                        notes=notes,
                        status='scheduled'
                    )

                    # Redirecionar para página de sucesso específica do agendamento público
                    return render(request, 'salons/booking_success.html', {
                        'salon': salon,
                        'appointment': appointment,
                        'token': token,
                        'is_public_booking': True
                    })

            except Exception as e:
                messages.error(request, f'Erro ao processar agendamento: {str(e)}')
                return render(request, 'salons/public_booking.html', {
                    'salon': salon, 'services': services, 'employees': employees, 'token': token
                })

        return render(request, 'salons/public_booking.html', {
            'salon': salon,
            'services': services,
            'employees': employees,
            'token': token,
            'today': timezone.now().date()
        })

    except BookingToken.DoesNotExist:
        messages.error(request, 'Link de agendamento inválido ou expirado.')
        return redirect('core:landing_page')