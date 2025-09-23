from django.db import models
from django.contrib.auth.models import User

class Salon(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome do Salão")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    photo = models.ImageField(upload_to='salon_photos/', blank=True, null=True, verbose_name="Foto do Salão")
    address = models.CharField(max_length=200, verbose_name="Endereço")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(max_length=2, verbose_name="Estado")
    zip_code = models.CharField(max_length=10, verbose_name="CEP")
    phone = models.CharField(max_length=15, verbose_name="Telefone")
    email = models.EmailField(verbose_name="Email")
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salon', verbose_name="Proprietário")
    
    # Horários de funcionamento simplificados
    weekdays_open = models.TimeField(blank=True, null=True, verbose_name="Segunda à Sexta - Abertura")
    weekdays_close = models.TimeField(blank=True, null=True, verbose_name="Segunda à Sexta - Fechamento")
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
        if 0 <= day_of_week <= 4:  # Segunda a sexta (0-4)
            return self.weekdays_open, self.weekdays_close
        elif day_of_week == 5:  # Sábado (5)
            return self.saturday_open, self.saturday_close
        elif day_of_week == 6:  # Domingo (6)
            return self.sunday_open, self.sunday_close
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

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', verbose_name="Usuário")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='employees', verbose_name="Salão")
    services = models.ManyToManyField(Service, blank=True, verbose_name="Serviços que pode executar")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    hire_date = models.DateField(auto_now_add=True, verbose_name="Data de contratação")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.salon.name}"
    
    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        unique_together = ['user', 'salon']


