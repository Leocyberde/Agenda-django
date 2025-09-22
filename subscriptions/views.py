from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Subscription

@login_required
def subscription_detail(request):
    """Mostra detalhes da assinatura do usuário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado. Apenas proprietários podem acessar esta página.')
        return redirect('accounts:dashboard')
    
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        defaults={'plan_type': 'trial_10'}
    )
    
    # Verificar se a assinatura expirou
    if not subscription.is_active() and subscription.status == 'active':
        subscription.status = 'expired'
        subscription.save()
    
    return render(request, 'subscriptions/detail.html', {
        'subscription': subscription
    })

@login_required
def renew_subscription(request):
    """Renova a assinatura do usuário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        
        if plan_type not in ['trial_10', 'vip_30']:
            messages.error(request, 'Plano inválido.')
            return redirect('subscriptions:detail')
        
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'plan_type': plan_type}
        )
        
        # Renovar a assinatura
        subscription.renew_subscription(plan_type)
        
        if plan_type == 'trial_10':
            messages.success(request, 'Plano teste renovado por mais 10 dias!')
        else:
            messages.success(request, 'Plano VIP ativado por 30 dias!')
        
        return redirect('subscriptions:detail')
    
    return render(request, 'subscriptions/renew.html')

@login_required
def upgrade_to_vip(request):
    """Upgrade para plano VIP"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')
    
    subscription, created = Subscription.objects.get_or_create(
        user=request.user,
        defaults={'plan_type': 'trial_10'}
    )
    
    if request.method == 'POST':
        # Simular processo de pagamento
        subscription.renew_subscription('vip_30')
        messages.success(request, 'Parabéns! Seu plano VIP foi ativado por 30 dias!')
        return redirect('subscriptions:detail')
    
    return render(request, 'subscriptions/upgrade.html', {
        'subscription': subscription
    })

def subscription_required(view_func):
    """Decorator para verificar se o usuário tem assinatura ativa"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if request.user.profile.user_type != 'owner':
            messages.error(request, 'Acesso negado.')
            return redirect('accounts:dashboard')
        
        subscription = getattr(request.user, 'subscription', None)
        if not subscription or not subscription.is_active():
            messages.warning(request, 'Sua assinatura expirou. Renove para continuar usando o sistema.')
            return redirect('subscriptions:detail')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
