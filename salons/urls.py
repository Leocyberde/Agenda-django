from django.urls import path
from . import views

app_name = 'salons'

urlpatterns = [
    # Dashboard e gestão do salão
    path('create/', views.create_salon, name='create_salon'),
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('edit/', views.edit_salon, name='edit_salon'),
    
    # Gestão de serviços
    path('services/', views.services_list, name='services_list'),
    path('services/create/', views.create_service, name='create_service'),
    path('services/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('services/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    
    # Agendamentos
    path('appointments/', views.appointments_list, name='appointments_list'),
    
    # Funcionários - Gerenciamento pelo proprietário
    path('employees/', views.employees_list, name='employees_list'),
    path('employees/create/', views.create_employee, name='create_employee'),
    path('employees/<int:employee_id>/edit/', views.edit_employee, name='edit_employee'),
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),
    
    # Painel do funcionário
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('employee/appointments/', views.employee_appointments, name='employee_appointments'),
    
    # Links de agendamento
    path('booking-link/generate/', views.generate_booking_link, name='generate_booking_link'),
    path('booking-link/toggle/', views.toggle_booking_link, name='toggle_booking_link'),
    
    # Agendamento público
    path('book/<str:token>/', views.public_booking, name='public_booking'),
]

