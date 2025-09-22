from django.contrib import admin
from .models import Salon, Service

@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'city', 'state', 'phone', 'created_at']
    list_filter = ['state', 'city', 'created_at']
    search_fields = ['name', 'owner__username', 'city', 'phone']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'salon', 'duration', 'price', 'is_active', 'created_at']
    list_filter = ['is_active', 'salon', 'created_at']
    search_fields = ['name', 'salon__name']
    readonly_fields = ['created_at', 'updated_at']
