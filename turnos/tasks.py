from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Reserva, Notificacion, Usuario

@shared_task
def enviar_email_confirmacion_reserva(reserva_id):
    """Enviar email de confirmación al cliente"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        asunto = f'Reserva Confirmada - {reserva.agenda.prestador.nombre_negocio}'
        mensaje = f"""
        Hola {reserva.cliente.nombre},
        
        Tu reserva ha sido confirmada exitosamente.
        
        Detalles de tu reserva:
        - Servicio: {reserva.servicio.nombre}
        - Fecha: {reserva.fecha.strftime('%d/%m/%Y')}
        - Hora: {reserva.hora_inicio.strftime('%H:%M')}
        - Lugar: {reserva.agenda.prestador.nombre_negocio}
        {f'- Dirección: {reserva.agenda.prestador.direccion}' if reserva.agenda.prestador.direccion else ''}
        
        Código de reserva: {reserva.codigo}
        
        Recuerda que puedes cancelar tu reserva hasta {reserva.agenda.prestador.horas_cancelacion_con_devolucion} horas antes para obtener reembolso completo.
        
        ¡Te esperamos!
        
        {reserva.agenda.prestador.nombre_negocio}
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [reserva.cliente.email],
            fail_silently=False,
        )
        
        # Crear notificación para el prestador
        if reserva.agenda.prestador.usuario:
            Notificacion.objects.create(
                usuario=reserva.agenda.prestador.usuario,
                tipo='nueva_reserva',
                titulo='Nueva Reserva',
                mensaje=f'Nueva reserva de {reserva.cliente.nombre} {reserva.cliente.apellido} para {reserva.servicio.nombre}',
                reserva=reserva
            )
        
        return True
    except Exception as e:
        print(f"Error enviando email de confirmación: {e}")
        return False

@shared_task
def enviar_email_cancelacion(reserva_id, motivo=''):
    """Enviar email de cancelación"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        asunto = f'Reserva Cancelada - {reserva.agenda.prestador.nombre_negocio}'
        mensaje = f"""
        Hola {reserva.cliente.nombre},
        
        Tu reserva ha sido cancelada.
        
        Detalles de la reserva cancelada:
        - Servicio: {reserva.servicio.nombre}
        - Fecha: {reserva.fecha.strftime('%d/%m/%Y')}
        - Hora: {reserva.hora_inicio.strftime('%H:%M')}
        - Código: {reserva.codigo}
        
        {f'Motivo: {motivo}' if motivo else ''}
        
        Si la cancelación fue realizada dentro del plazo permitido, el reembolso se procesará en los próximos días.
        
        Puedes hacer una nueva reserva cuando lo desees.
        
        {reserva.agenda.prestador.nombre_negocio}
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [reserva.cliente.email],
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error enviando email de cancelación: {e}")
        return False

@shared_task
def enviar_recordatorios_diarios():
    """Enviar recordatorios de reservas para el día siguiente"""
    mañana = timezone.now().date() + timedelta(days=1)
    
    reservas = Reserva.objects.filter(
        fecha=mañana,
        estado='confirmada'
    ).select_related('cliente', 'servicio', 'agenda__prestador')
    
    for reserva in reservas:
        try:
            asunto = f'Recordatorio: Tu reserva es mañana'
            mensaje = f"""
            Hola {reserva.cliente.nombre},
            
            Te recordamos que tienes una reserva para mañana.
            
            Detalles:
            - Servicio: {reserva.servicio.nombre}
            - Fecha: {reserva.fecha.strftime('%d/%m/%Y')}
            - Hora: {reserva.hora_inicio.strftime('%H:%M')}
            - Lugar: {reserva.agenda.prestador.nombre_negocio}
            {f'- Dirección: {reserva.agenda.prestador.direccion}' if reserva.agenda.prestador.direccion else ''}
            
            ¡Te esperamos!
            
            {reserva.agenda.prestador.nombre_negocio}
            """
            
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [reserva.cliente.email],
                fail_silently=True,
            )
            
            # Crear notificación
            if reserva.cliente.usuario:
                Notificacion.objects.create(
                    usuario=reserva.cliente.usuario,
                    tipo='recordatorio',
                    titulo='Recordatorio de Reserva',
                    mensaje=f'Tu reserva es mañana a las {reserva.hora_inicio.strftime("%H:%M")}',
                    reserva=reserva
                )
        except Exception as e:
            print(f"Error enviando recordatorio para reserva {reserva.id}: {e}")
    
    return f"Enviados {len(reservas)} recordatorios"

@shared_task
def marcar_reservas_no_asistidas():
    """Marcar reservas como 'no_asistio' después de la hora programada"""
    ayer = timezone.now().date() - timedelta(days=1)
    
    reservas = Reserva.objects.filter(
        fecha=ayer,
        estado='confirmada'
    )
    
    cantidad = reservas.update(estado='no_asistio')
    
    return f"Marcadas {cantidad} reservas como no asistidas"

@shared_task
def limpiar_notificaciones_antiguas():
    """Eliminar notificaciones leídas con más de 30 días"""
    hace_30_dias = timezone.now() - timedelta(days=30)
    
    cantidad = Notificacion.objects.filter(
        leida=True,
        fecha_creacion__lt=hace_30_dias
    ).delete()[0]
    
    return f"Eliminadas {cantidad} notificaciones antiguas"

@shared_task
def generar_reporte_diario_prestador(prestador_id):
    """Generar y enviar reporte diario al prestador"""
    from .models import PerfilPrestador
    
    try:
        prestador = PerfilPrestador.objects.get(id=prestador_id)
        hoy = timezone.now().date()
        
        reservas_hoy = Reserva.objects.filter(
            agenda__prestador=prestador,
            fecha=hoy
        ).select_related('cliente', 'servicio')
        
        if not reservas_hoy.exists():
            return "No hay reservas para hoy"
        
        # Construir mensaje
        mensaje = f"""
        Buenos días,
        
        Reporte de turnos para hoy {hoy.strftime('%d/%m/%Y')}:
        
        Total de reservas: {reservas_hoy.count()}
        
        Detalle:
        """
        
        for reserva in reservas_hoy.order_by('hora_inicio'):
            estado_emoji = {
                'confirmada': '✅',
                'pendiente': '⏳',
                'cancelada': '❌'
            }.get(reserva.estado, '❓')
            
            mensaje += f"""
        {estado_emoji} {reserva.hora_inicio.strftime('%H:%M')} - {reserva.cliente.nombre} {reserva.cliente.apellido}
           Servicio: {reserva.servicio.nombre}
           Tel: {reserva.cliente.telefono or 'N/A'}
        """
        
        # Calcular ingresos esperados
        ingresos = sum(r.monto_pagado for r in reservas_hoy if r.estado in ['confirmada', 'completada'])
        mensaje += f"\n\nIngresos del día: ${ingresos}"
        
        # Enviar email
        send_mail(
            f'Reporte Diario - {hoy.strftime("%d/%m/%Y")}',
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [prestador.usuario.email],
            fail_silently=True,
        )
        
        # Crear notificación
        Notificacion.objects.create(
            usuario=prestador.usuario,
            tipo='recordatorio',
            titulo='Reporte Diario',
            mensaje=f'Tienes {reservas_hoy.count()} reservas para hoy'
        )
        
        return f"Reporte enviado a {prestador.nombre_negocio}"
    except Exception as e:
        print(f"Error generando reporte diario: {e}")
        return f"Error: {e}"

@shared_task
def procesar_devolucion_mercadopago(reserva_id):
    """Procesar devolución en MercadoPago"""
    try:
        import mercadopago
        reserva = Reserva.objects.get(id=reserva_id)
        prestador = reserva.agenda.prestador
        
        if not reserva.mp_payment_id:
            return "No hay pago asociado"
        
        # Verificar si corresponde devolución
        if not reserva.puede_cancelar_con_devolucion():
            return "No corresponde devolución por política de cancelación"
        
        # Procesar devolución
        sdk = mercadopago.SDK(prestador.mp_access_token)
        refund = sdk.refund().create(reserva.mp_payment_id)
        
        if refund["status"] == 201:
            reserva.estado_pago = 'devuelto'
            reserva.save()
            
            # Notificar al cliente
            enviar_email_devolucion.delay(reserva_id)
            
            return "Devolución procesada exitosamente"
        else:
            return f"Error procesando devolución: {refund}"
    except Exception as e:
        print(f"Error procesando devolución: {e}")
        return f"Error: {e}"

@shared_task
def enviar_email_devolucion(reserva_id):
    """Enviar email confirmando devolución"""
    try:
        reserva = Reserva.objects.get(id=reserva_id)
        
        asunto = 'Devolución Procesada'
        mensaje = f"""
        Hola {reserva.cliente.nombre},
        
        Te informamos que se ha procesado la devolución de tu reserva cancelada.
        
        Detalles:
        - Código de reserva: {reserva.codigo}
        - Monto devuelto: ${reserva.monto_pagado}
        
        El reembolso será acreditado en tu medio de pago en los próximos 5 a 10 días hábiles.
        
        Gracias por tu comprensión.
        
        {reserva.agenda.prestador.nombre_negocio}
        """
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [reserva.cliente.email],
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error enviando email de devolución: {e}")
        return False

@shared_task
def sincronizar_con_google_calendar(reserva_id):
    """Sincronizar reserva con Google Calendar (implementación futura)"""
    # TODO: Implementar integración con Google Calendar API
    pass