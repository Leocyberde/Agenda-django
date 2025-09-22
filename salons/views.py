from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from subscriptions.views import subscription_required
from .models import Salon, Service
from .forms import SalonForm, ServiceForm
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
        form = SalonForm(request.POST)
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
        form = SalonForm(request.POST, instance=salon)
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
