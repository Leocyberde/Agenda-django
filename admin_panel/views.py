
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import UserProfile
from salons.models import Salon, Service
from subscriptions.models import Subscription
from appointments.models import Appointment

def is_admin_user(user):
    """Verifica se o usuário é superusuário (administrador)"""
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Dashboard principal do administrador"""
    # Estatísticas gerais
    total_owners = UserProfile.objects.filter(user_type='owner').count()
    total_clients = UserProfile.objects.filter(user_type='client').count()
    total_salons = Salon.objects.count()
    total_appointments = Appointment.objects.count()
    
    # Assinaturas ativas e expiradas
    active_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__gt=timezone.now()
    ).count()
    
    expired_subscriptions = Subscription.objects.filter(
        Q(status='expired') | Q(end_date__lte=timezone.now())
    ).count()
    
    # Assinaturas expirando em 3 dias
    expiring_soon = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now() + timedelta(days=3),
        end_date__gt=timezone.now()
    ).count()
    
    # Últimos comerciantes cadastrados
    recent_owners = UserProfile.objects.filter(
        user_type='owner'
    ).select_related('user').order_by('-created_at')[:5]
    
    # Comerciantes com assinaturas expirando
    expiring_subscriptions = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now() + timedelta(days=7),
        end_date__gt=timezone.now()
    ).select_related('user').order_by('end_date')[:10]
    
    context = {
        'total_owners': total_owners,
        'total_clients': total_clients,
        'total_salons': total_salons,
        'total_appointments': total_appointments,
        'active_subscriptions': active_subscriptions,
        'expired_subscriptions': expired_subscriptions,
        'expiring_soon': expiring_soon,
        'recent_owners': recent_owners,
        'expiring_subscriptions': expiring_subscriptions,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def manage_owners(request):
    """Gerenciar comerciantes"""
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    owners = UserProfile.objects.filter(user_type='owner').select_related('user')
    
    if search:
        owners = owners.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    if status_filter == 'active':
        owners = owners.filter(user__subscription__status='active')
    elif status_filter == 'expired':
        owners = owners.filter(
            Q(user__subscription__status='expired') |
            Q(user__subscription__end_date__lte=timezone.now())
        )
    
    owners = owners.order_by('-created_at')
    
    return render(request, 'admin_panel/manage_owners.html', {
        'owners': owners,
        'search': search,
        'status_filter': status_filter,
    })

@login_required
@user_passes_test(is_admin_user)
def owner_detail(request, owner_id):
    """Detalhes de um comerciante específico"""
    owner = get_object_or_404(UserProfile, id=owner_id, user_type='owner')
    
    # Informações do salão
    salon = getattr(owner.user, 'salon', None)
    
    # Assinatura
    subscription = getattr(owner.user, 'subscription', None)
    
    # Estatísticas
    if salon:
        total_services = salon.services.filter(is_active=True).count()
        total_appointments = Appointment.objects.filter(salon=salon).count()
        pending_appointments = Appointment.objects.filter(
            salon=salon, 
            status='scheduled'
        ).count()
    else:
        total_services = 0
        total_appointments = 0
        pending_appointments = 0
    
    return render(request, 'admin_panel/owner_detail.html', {
        'owner': owner,
        'salon': salon,
        'subscription': subscription,
        'total_services': total_services,
        'total_appointments': total_appointments,
        'pending_appointments': pending_appointments,
    })

@login_required
@user_passes_test(is_admin_user)
def manage_subscription(request, owner_id):
    """Gerenciar assinatura de um comerciante"""
    owner = get_object_or_404(UserProfile, id=owner_id, user_type='owner')
    subscription, created = Subscription.objects.get_or_create(
        user=owner.user,
        defaults={'plan_type': 'trial_10'}
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'renew':
            plan_type = request.POST.get('plan_type')
            if plan_type in ['trial_10', 'vip_30']:
                subscription.renew_subscription(plan_type)
                messages.success(request, f'Assinatura renovada para {subscription.get_plan_type_display()}!')
        
        elif action == 'extend':
            days = int(request.POST.get('days', 0))
            if days > 0:
                subscription.end_date += timedelta(days=days)
                subscription.save()
                messages.success(request, f'Assinatura estendida por {days} dias!')
        
        elif action == 'cancel':
            subscription.status = 'cancelled'
            subscription.save()
            messages.success(request, 'Assinatura cancelada!')
        
        elif action == 'activate':
            subscription.status = 'active'
            subscription.save()
            messages.success(request, 'Assinatura ativada!')
        
        elif action == 'fix_to_vip':
            subscription.renew_subscription('vip_30')
            messages.success(request, 'Assinatura corrigida para VIP 30 dias!')
        
        return redirect('admin_panel:owner_detail', owner_id=owner.id)
    
    return render(request, 'admin_panel/manage_subscription.html', {
        'owner': owner,
        'subscription': subscription,
    })

@login_required
@user_passes_test(is_admin_user)
def subscription_reports(request):
    """Relatórios de assinaturas"""
    # Assinaturas por tipo
    trial_count = Subscription.objects.filter(plan_type='trial_10').count()
    vip_count = Subscription.objects.filter(plan_type='vip_30').count()
    
    # Assinaturas por status
    active_count = Subscription.objects.filter(status='active').count()
    expired_count = Subscription.objects.filter(status='expired').count()
    cancelled_count = Subscription.objects.filter(status='cancelled').count()
    
    # Receita estimada (simulação)
    monthly_revenue = vip_count * 50  # Assumindo R$ 50 por plano VIP
    
    # Assinaturas expirando nos próximos 7 dias
    expiring_soon = Subscription.objects.filter(
        status='active',
        end_date__lte=timezone.now() + timedelta(days=7),
        end_date__gt=timezone.now()
    ).select_related('user').order_by('end_date')
    
    return render(request, 'admin_panel/subscription_reports.html', {
        'trial_count': trial_count,
        'vip_count': vip_count,
        'active_count': active_count,
        'expired_count': expired_count,
        'cancelled_count': cancelled_count,
        'monthly_revenue': monthly_revenue,
        'expiring_soon': expiring_soon,
    })
