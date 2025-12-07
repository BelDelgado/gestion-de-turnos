from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from turnos import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Home
    path('', views.home, name='home'),
    
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='turnos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro_prestador, name='registro'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='turnos/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='turnos/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='turnos/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='turnos/password_reset_complete.html'),
         name='password_reset_complete'),
    
    # Dashboard Prestador
    path('dashboard/', views.dashboard_prestador, name='dashboard_prestador'),
    path('perfil/', views.perfil_prestador_view, name='perfil_prestador'),
    
    # Servicios
    path('servicios/', views.servicios_list, name='servicios_list'),
    path('servicios/nuevo/', views.servicio_create, name='servicio_create'),
    path('servicios/<int:pk>/editar/', views.servicio_update, name='servicio_update'),
    path('servicios/<int:pk>/eliminar/', views.servicio_delete, name='servicio_delete'),
    
    # Clientes
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('clientes/<int:pk>/bloquear/', views.cliente_toggle_bloqueo, name='cliente_toggle_bloqueo'),
    
    # Reservas
    path('reservas/', views.reservas_list, name='reservas_list'),
    path('reservas/<int:pk>/cancelar/', views.reserva_cancelar, name='reserva_cancelar'),
    
    # API para disponibilidad
    path('api/disponibilidad/', views.disponibilidad_ajax, name='disponibilidad_ajax'),
    path('api/reserva/', views.procesar_reserva, name='procesar_reserva'),
    
    # Reservas públicas
    path('reservar/<slug:slug>/', views.reserva_publica, name='reserva_publica'),
    path('reserva/comprobante/<uuid:codigo>/', views.reserva_comprobante_pdf, name='reserva_comprobante'),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)