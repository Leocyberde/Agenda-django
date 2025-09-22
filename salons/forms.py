from django import forms
from .models import Salon, Service

class SalonForm(forms.ModelForm):
    class Meta:
        model = Salon
        fields = [
            'name', 'description', 'address', 'city', 'state', 'zip_code', 
            'phone', 'email',
            'monday_open', 'monday_close',
            'tuesday_open', 'tuesday_close',
            'wednesday_open', 'wednesday_close',
            'thursday_open', 'thursday_close',
            'friday_open', 'friday_close',
            'saturday_open', 'saturday_close',
            'sunday_open', 'sunday_close'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do salão'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do salão'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Endereço completo'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UF', 'maxlength': 2}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CEP'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(11) 99999-9999'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'monday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'monday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tuesday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tuesday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'wednesday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'wednesday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'thursday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'thursday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'friday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'friday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'saturday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'saturday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sunday_open': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'sunday_close': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'duration', 'price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do serviço'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do serviço'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duração em minutos', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].label = 'Serviço ativo'

