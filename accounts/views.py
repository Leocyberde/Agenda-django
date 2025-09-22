from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm, UserProfileForm
from .models import UserProfile

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        messages.success(self.request, 'Conta criada com sucesso! Faça login para continuar.')
        return response

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Conta criada com sucesso! Faça login para continuar.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile
    })

@login_required
def dashboard_view(request):
    """Dashboard principal que redireciona baseado no tipo de usuário"""
    # Verificar se é administrador (superusuário)
    if request.user.is_superuser:
        return redirect('admin_panel:dashboard')
    
    profile = request.user.profile
    
    if profile.user_type == 'owner':
        # Verificar se tem salão cadastrado
        if hasattr(request.user, 'salon'):
            return redirect('salons:owner_dashboard')
        else:
            return redirect('salons:create_salon')
    else:
        return redirect('appointments:client_dashboard')

@login_required
def subscription_status(request):
    """Mostra status da assinatura do usuário"""
    if request.user.profile.user_type != 'owner':
        messages.error(request, 'Acesso negado.')
        return redirect('accounts:dashboard')
    
    subscription = getattr(request.user, 'subscription', None)
    
    return render(request, 'accounts/subscription_status.html', {
        'subscription': subscription
    })

def logout_view(request):
    """Custom logout view that accepts GET requests"""
    logout(request)
    messages.success(request, 'Você saiu do sistema com sucesso!')
    return redirect('core:landing_page')
