from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Main dashboard (single page)
    path('', views.dashboard, name='dashboard'),

    # Data ingestion
    path('api/ingest/', views.ingest, name='ingest'),

    # JSON API for AJAX polling
    path('api/hosts/', views.api_hosts, name='api_hosts'),
    path('api/hosts/<int:host_id>/', views.api_host_detail, name='api_host_detail'),
    path('api/anomalies/', views.api_anomalies, name='api_anomalies'),

    # Advice engine
    path('api/advice/', views.api_advice, name='api_advice'),

    # Website monitoring
    path('api/websites/', views.api_websites, name='api_websites'),
    path('api/websites/<int:monitor_id>/', views.api_website_detail, name='api_website_detail'),

    # Device & website management
    path('api/add-host/', views.api_add_host, name='api_add_host'),
    path('api/add-website/', views.api_add_website, name='api_add_website'),
    path('api/websites/<int:monitor_id>/delete/', views.api_delete_website, name='api_delete_website'),
    path('api/websites/<int:monitor_id>/edit/', views.api_edit_website, name='api_edit_website'),
    path('api/hosts/<int:host_id>/rename/', views.api_rename_host, name='api_rename_host'),
    path('api/hosts/<int:host_id>/delete/', views.api_delete_host, name='api_delete_host'),
    path('api/set-webhook/', views.api_set_webhook, name='api_set_webhook'),
]
