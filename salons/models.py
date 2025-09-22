from django.db import models
from django.contrib.auth.models import User

class Salon(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome do Salão")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    address = models.CharField(max_length=200, verbose_name="Endereço")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="Estado")
    zip_code = models.CharField(max_length=10, verbose_name="CEP")
    phone = models.CharField(max_length=15, verbose_name="Telefone")
    email = models.EmailField(verbose_name="Email")
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salon', verbose_name="Proprietário")
    
    # Horários de funcionamento
    monday_open = models.TimeField(blank=True, null=True, verbose_name="Segunda - Abertura")
    monday_close = models.TimeField(blank=True, null=True, verbose_name="Segunda - Fechamento")
    tuesday_open = models.TimeField(blank=True, null=True, verbose_name="Terça - Abertura")
    tuesday_close = models.TimeField(blank=True, null=True, verbose_name="Terça - Fechamento")
    wednesday_open = models.TimeField(blank=True, null=True, verbose_name="Quarta - Abertura")
    wednesday_close = models.TimeField(blank=True, null=True, verbose_name="Quarta - Fechamento")
    thursday_open = models.TimeField(blank=True, null=True, verbose_name="Quinta - Abertura")
    thursday_close = models.TimeField(blank=True, null=True, verbose_name="Quinta - Fechamento")
    friday_open = models.TimeField(blank=True, null=True, verbose_name="Sexta - Abertura")
    friday_close = models.TimeField(blank=True, null=True, verbose_name="Sexta - Fechamento")
    saturday_open = models.TimeField(blank=True, null=True, verbose_name="Sábado - Abertura")
    saturday_close = models.TimeField(blank=True, null=True, verbose_name="Sábado - Fechamento")
    sunday_open = models.TimeField(blank=True, null=True, verbose_name="Domingo - Abertura")
    sunday_close = models.TimeField(blank=True, null=True, verbose_name="Domingo - Fechamento")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    def get_working_hours(self, day_of_week):
        """Retorna horário de funcionamento para um dia específico (0=segunda, 6=domingo)"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if 0 <= day_of_week <= 6:
            day_name = days[day_of_week]
            open_time = getattr(self, f"{day_name}_open")
            close_time = getattr(self, f"{day_name}_close")
            return open_time, close_time
        return None, None
    
    class Meta:
        verbose_name = "Salão"
        verbose_name_plural = "Salões"

class Service(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='services', verbose_name="Salão")
    name = models.CharField(max_length=100, verbose_name="Nome do Serviço")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    duration = models.PositiveIntegerField(verbose_name="Duração (minutos)")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.salon.name} - {self.name}"
    
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ['name']
