from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid

class Usuario(AbstractUser):
    """Usuario extendido con roles"""
    ROLES = (
        ('admin', 'Administrador'),
        ('prestador', 'Prestador de Servicio'),
        ('cliente', 'Cliente'),
    )
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    dni = models.CharField(max_length=20, unique=True, blank=True, null=True)
    google_id = models.CharField(max_length=255, blank=True, null=True)
    bloqueado = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'usuarios'

class PerfilPrestador(models.Model):
    """Perfil del prestador de servicios"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_prestador')
    nombre_negocio = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    # Configuración de pagos
    mp_access_token = models.CharField(max_length=500, blank=True)
    mp_public_key = models.CharField(max_length=500, blank=True)
    requiere_pago_total = models.BooleanField(default=False)
    porcentaje_seña = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    
    # Políticas de cancelación
    horas_cancelacion_con_devolucion = models.IntegerField(default=24)
    horas_cancelacion_sin_devolucion = models.IntegerField(default=2)
    
    # Link único para reservas
    slug = models.SlugField(unique=True)
    
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'perfiles_prestadores'
        verbose_name_plural = 'Perfiles de Prestadores'
    
    def __str__(self):
        return self.nombre_negocio

class Agenda(models.Model):
    """Agenda de un prestador (puede tener múltiples)"""
    prestador = models.ForeignKey(PerfilPrestador, on_delete=models.CASCADE, related_name='agendas')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    # Horarios de atención
    hora_inicio = models.TimeField(default='09:00')
    hora_fin = models.TimeField(default='18:00')
    
    # Días laborables
    lunes = models.BooleanField(default=True)
    martes = models.BooleanField(default=True)
    miercoles = models.BooleanField(default=True)
    jueves = models.BooleanField(default=True)
    viernes = models.BooleanField(default=True)
    sabado = models.BooleanField(default=False)
    domingo = models.BooleanField(default=False)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'agendas'
    
    def __str__(self):
        return f"{self.nombre} - {self.prestador.nombre_negocio}"

class Servicio(models.Model):
    """Servicios ofrecidos por el prestador"""
    CATEGORIAS = (
        ('uñas', 'Uñas'),
        ('pestañas', 'Pestañas'),
        ('pelo', 'Peluquería'),
        ('barberia', 'Barbería'),
        ('veterinaria', 'Veterinaria'),
        ('masajes', 'Masajes'),
        ('estetica', 'Estética'),
        ('otro', 'Otro'),
    )
    
    prestador = models.ForeignKey(PerfilPrestador, on_delete=models.CASCADE, related_name='servicios')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    duracion_minutos = models.IntegerField(validators=[MinValueValidator(15)])
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'servicios'
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

class Cliente(models.Model):
    """Ficha de clientes"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    prestador = models.ForeignKey(PerfilPrestador, on_delete=models.CASCADE, related_name='clientes')
    
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    dni = models.CharField(max_length=20)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    
    notas = models.TextField(blank=True)
    bloqueado = models.BooleanField(default=False)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultima_visita = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'clientes'
        unique_together = ['prestador', 'dni']
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Reserva(models.Model):
    """Reservas/Turnos"""
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
        ('no_asistio', 'No Asistió'),
    )
    
    ESTADO_PAGO = (
        ('pendiente', 'Pendiente'),
        ('seña', 'Seña Pagada'),
        ('total', 'Pagado Total'),
        ('devuelto', 'Devuelto'),
    )
    
    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    agenda = models.ForeignKey(Agenda, on_delete=models.CASCADE, related_name='reservas')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO, default='pendiente')
    
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Datos de pago
    mp_payment_id = models.CharField(max_length=200, blank=True, null=True)
    mp_preference_id = models.CharField(max_length=200, blank=True, null=True)
    
    notas = models.TextField(blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(blank=True, null=True)
    motivo_cancelacion = models.TextField(blank=True)
    
    class Meta:
        db_table = 'reservas'
        ordering = ['fecha', 'hora_inicio']
    
    def __str__(self):
        return f"Reserva {self.codigo} - {self.cliente} - {self.fecha}"
    
    def puede_cancelar_con_devolucion(self):
        """Verifica si puede cancelar con devolución"""
        prestador = self.agenda.prestador
        horas_limite = prestador.horas_cancelacion_con_devolucion
        fecha_hora_reserva = timezone.make_aware(
            timezone.datetime.combine(self.fecha, self.hora_inicio)
        )
        diferencia = fecha_hora_reserva - timezone.now()
        return diferencia.total_seconds() / 3600 >= horas_limite

class Notificacion(models.Model):
    """Sistema de notificaciones"""
    TIPOS = (
        ('nueva_reserva', 'Nueva Reserva'),
        ('cancelacion', 'Cancelación'),
        ('recordatorio', 'Recordatorio'),
        ('pago', 'Pago Recibido'),
    )
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=30, choices=TIPOS)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, null=True, blank=True)
    
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notificaciones'
        ordering = ['-fecha_creacion']

class ConfiguracionGlobal(models.Model):
    """Configuraciones globales del sistema"""
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    
    class Meta:
        db_table = 'configuracion_global'
        verbose_name_plural = 'Configuraciones Globales'