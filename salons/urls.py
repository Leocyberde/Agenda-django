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
]

