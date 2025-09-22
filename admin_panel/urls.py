
from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('owners/', views.manage_owners, name='manage_owners'),
    path('owners/<int:owner_id>/', views.owner_detail, name='owner_detail'),
    path('owners/<int:owner_id>/subscription/', views.manage_subscription, name='manage_subscription'),
    path('reports/', views.subscription_reports, name='subscription_reports'),
]
