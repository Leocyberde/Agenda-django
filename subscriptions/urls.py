from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_detail, name='detail'),
    path('renew/', views.renew_subscription, name='renew'),
    path('upgrade/', views.upgrade_to_vip, name='upgrade'),
]

