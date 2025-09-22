from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    user_type = forms.ChoiceField(
        choices=UserProfile.USER_TYPES,
        required=True,
        label="Tipo de Usuário",
        widget=forms.RadioSelect
    )
    phone = forms.CharField(max_length=15, required=False, label="Telefone")
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customizar labels e placeholders
        self.fields['username'].label = "Nome de usuário"
        self.fields['password1'].label = "Senha"
        self.fields['password2'].label = "Confirmar senha"
        
        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Atualizar o perfil do usuário
            profile = user.profile
            profile.user_type = self.cleaned_data['user_type']
            profile.phone = self.cleaned_data['phone']
            profile.save()
            
            # Criar assinatura automática para proprietários
            if self.cleaned_data['user_type'] == 'owner':
                from subscriptions.models import Subscription
                Subscription.objects.create(user=user, plan_type='trial_10')
        
        return user

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nome")
    last_name = forms.CharField(max_length=30, required=True, label="Sobrenome")
    email = forms.EmailField(required=True, label="Email")
    
    class Meta:
        model = UserProfile
        fields = ['phone', 'birth_date', 'profile_picture']
        labels = {
            'phone': 'Telefone',
            'birth_date': 'Data de Nascimento',
            'profile_picture': 'Foto de Perfil',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Preencher campos do usuário se existir instância
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if commit:
            # Atualizar dados do usuário
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
            
            profile.save()
        
        return profile

