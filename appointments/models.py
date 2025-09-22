from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from salons.models import Salon, Service

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Agendado'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Concluído'),
        ('no_show', 'Não compareceu'),
    )
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments', verbose_name="Cliente")
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE, related_name='appointments', verbose_name="Salão")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='appointments', verbose_name="Serviço")
    employee = models.ForeignKey('salons.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments', verbose_name="Funcionário responsável")
    appointment_date = models.DateField(verbose_name="Data do Agendamento")
    appointment_time = models.TimeField(verbose_name="Horário do Agendamento")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled', verbose_name="Status")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.client.username} - {self.salon.name} - {self.appointment_date} {self.appointment_time}"
    
    def can_be_cancelled(self):
        """Verifica se o agendamento pode ser cancelado (até 2 horas antes)"""
        from datetime import datetime, timedelta
        appointment_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        appointment_datetime = timezone.make_aware(appointment_datetime)
        cutoff_time = appointment_datetime - timedelta(hours=2)
        return timezone.now() < cutoff_time and self.status in ['scheduled', 'confirmed']
    
    def get_end_time(self):
        """Calcula o horário de término baseado na duração do serviço"""
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.appointment_date, self.appointment_time)
        end_datetime = start_datetime + timedelta(minutes=self.service.duration)
        return end_datetime.time()
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['appointment_date', 'appointment_time']
        constraints = [
            models.UniqueConstraint(
                fields=['salon', 'employee', 'appointment_date', 'appointment_time'],
                condition=models.Q(employee__isnull=False),
                name='unique_employee_appointment_time'
            ),
            models.UniqueConstraint(
                fields=['salon', 'appointment_date', 'appointment_time'],
                condition=models.Q(employee__isnull=True),
                name='unique_salon_appointment_time_no_employee'
            )
        ]
