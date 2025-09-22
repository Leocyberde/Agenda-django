from django import forms
from django.contrib.auth.models import User
from .models import Salon, Service, Employee

class SalonForm(forms.ModelForm):
    class Meta:
        model = Salon
        exclude = ['owner']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            
            # Horários simplificados
            'weekdays_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'weekdays_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'saturday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'saturday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sunday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sunday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        exclude = ['salon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EmployeeForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        min_length=8,
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = ['services', 'is_active']
        widgets = {
            'services': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        salon = kwargs.pop('salon', None)
        super().__init__(*args, **kwargs)
        if salon:
            self.fields['services'].queryset = salon.services.all()
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Um usuário com este email já existe.")
        return email

class EmployeeEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        label="Nome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30, 
        label="Sobrenome",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Employee
        fields = ['services', 'is_active']
        widgets = {
            'services': forms.CheckboxSelectMultiple(),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        salon = kwargs.pop('salon', None)
        super().__init__(*args, **kwargs)
        if salon:
            self.fields['services'].queryset = salon.services.all()
        if self.instance and self.instance.pk:
            # Preencher campos do usuário
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.instance and self.instance.pk:
            # Permitir o mesmo email do usuário atual
            if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                raise forms.ValidationError("Um usuário com este email já existe.")
        else:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("Um usuário com este email já existe.")
        return email
    
    def save(self, commit=True):
        employee = super().save(commit=False)
        if commit:
            # Atualizar dados do usuário
            user = employee.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.username = self.cleaned_data['email']  # Usar email como username
            user.save()
            employee.save()
            self.save_m2m()  # Salvar many-to-many relationships
        return employee