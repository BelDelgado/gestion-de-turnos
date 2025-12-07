from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta, time
import mercadopago
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import json

from .models import (
    Usuario, PerfilPrestador, Agenda, Servicio, 
    Cliente, Reserva, Notificacion
)
from .forms import (
    RegistroForm, PerfilPrestadorForm, ServicioForm,
    AgendaForm, ClienteForm, ReservaForm
)

# ==================== VISTAS PÚBLICAS ====================

def home(request):
    """Página de inicio"""
    return render(request, 'turnos/home.html')

def registro_prestador(request):
    """Registro de nuevo prestador"""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = 'prestador'
            user.save()
            
            # Crear perfil prestador
            PerfilPrestador.objects.create(
                usuario=user,
                nombre_negocio=form.cleaned_data['nombre_negocio'],
                slug=form.cleaned_data['slug']
            )
            
            login(request, user)
            messages.success(request, '¡Registro exitoso! Completa tu perfil.')
            return redirect('perfil_prestador')
    else:
        form = RegistroForm()
    
    return render(request, 'turnos/registro.html', {'form': form})

# ==================== VISTAS PRESTADOR ====================

@login_required
def dashboard_prestador(request):
    """Panel principal del prestador"""
    if request.user.rol != 'prestador':
        messages.error(request, 'No tienes permisos para acceder.')
        return redirect('home')
    
    perfil = request.user.perfil_prestador
    hoy = timezone.now().date()
    
    # Estadísticas
    reservas_hoy = Reserva.objects.filter(
        agenda__prestador=perfil,
        fecha=hoy,
        estado='confirmada'
    ).count()
    
    reservas_pendientes = Reserva.objects.filter(
        agenda__prestador=perfil,
        estado='pendiente'
    ).count()
    
    ingresos_mes = Reserva.objects.filter(
        agenda__prestador=perfil,
        fecha__month=hoy.month,
        fecha__year=hoy.year,
        estado__in=['confirmada', 'completada']
    ).aggregate(total=Sum('monto_pagado'))['total'] or 0
    
    proximas_reservas = Reserva.objects.filter(
        agenda__prestador=perfil,
        fecha__gte=hoy,
        estado='confirmada'
    ).select_related('cliente', 'servicio', 'agenda').order_by('fecha', 'hora_inicio')[:10]
    
    context = {
        'perfil': perfil,
        'reservas_hoy': reservas_hoy,
        'reservas_pendientes': reservas_pendientes,
        'ingresos_mes': ingresos_mes,
        'proximas_reservas': proximas_reservas,
    }
    
    return render(request, 'turnos/dashboard_prestador.html', context)

@login_required
def perfil_prestador_view(request):
    """Gestión del perfil del prestador"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    perfil = request.user.perfil_prestador
    
    if request.method == 'POST':
        form = PerfilPrestadorForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_prestador')
    else:
        form = PerfilPrestadorForm(instance=perfil)
    
    return render(request, 'turnos/perfil_prestador.html', {'form': form, 'perfil': perfil})

@login_required
def servicios_list(request):
    """Lista de servicios del prestador"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    perfil = request.user.perfil_prestador
    servicios = perfil.servicios.all()
    
    return render(request, 'turnos/servicios_list.html', {'servicios': servicios})

@login_required
def servicio_create(request):
    """Crear nuevo servicio"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.prestador = request.user.perfil_prestador
            servicio.save()
            messages.success(request, 'Servicio creado exitosamente.')
            return redirect('servicios_list')
    else:
        form = ServicioForm()
    
    return render(request, 'turnos/servicio_form.html', {'form': form})

@login_required
def servicio_update(request, pk):
    """Actualizar servicio"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    servicio = get_object_or_404(Servicio, pk=pk, prestador=request.user.perfil_prestador)
    
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio actualizado.')
            return redirect('servicios_list')
    else:
        form = ServicioForm(instance=servicio)
    
    return render(request, 'turnos/servicio_form.html', {'form': form, 'servicio': servicio})

@login_required
def servicio_delete(request, pk):
    """Eliminar servicio"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    servicio = get_object_or_404(Servicio, pk=pk, prestador=request.user.perfil_prestador)
    servicio.delete()
    messages.success(request, 'Servicio eliminado.')
    return redirect('servicios_list')

@login_required
def clientes_list(request):
    """Ficha de clientes"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    perfil = request.user.perfil_prestador
    clientes = perfil.clientes.all().order_by('-fecha_registro')
    
    # Búsqueda
    q = request.GET.get('q')
    if q:
        clientes = clientes.filter(
            Q(nombre__icontains=q) |
            Q(apellido__icontains=q) |
            Q(dni__icontains=q) |
            Q(email__icontains=q)
        )
    
    return render(request, 'turnos/clientes_list.html', {'clientes': clientes})

@login_required
def cliente_detail(request, pk):
    """Detalle del cliente"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk, prestador=request.user.perfil_prestador)
    reservas = cliente.reservas.all().order_by('-fecha')
    
    # Calcular estadísticas
    total_gastado = reservas.filter(
        estado__in=['confirmada', 'completada']
    ).aggregate(total=Sum('monto_pagado'))['total'] or 0
    
    context = {
        'cliente': cliente,
        'reservas': reservas,
        'total_gastado': total_gastado,
    }
    
    return render(request, 'turnos/cliente_detail.html', context)

@login_required
def cliente_toggle_bloqueo(request, pk):
    """Bloquear/desbloquear cliente"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk, prestador=request.user.perfil_prestador)
    cliente.bloqueado = not cliente.bloqueado
    cliente.save()
    
    estado = "bloqueado" if cliente.bloqueado else "desbloqueado"
    messages.success(request, f'Cliente {estado}.')
    return redirect('cliente_detail', pk=pk)

@login_required
def reservas_list(request):
    """Lista de reservas"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    perfil = request.user.perfil_prestador
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    
    reservas = Reserva.objects.filter(
        agenda__prestador=perfil
    ).select_related('cliente', 'servicio', 'agenda')
    
    if fecha_desde:
        reservas = reservas.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        reservas = reservas.filter(fecha__lte=fecha_hasta)
    if estado:
        reservas = reservas.filter(estado=estado)
    
    reservas = reservas.order_by('-fecha', '-hora_inicio')
    
    return render(request, 'turnos/reservas_list.html', {'reservas': reservas})

@login_required
def reserva_cancelar(request, pk):
    """Cancelar reserva"""
    if request.user.rol != 'prestador':
        return redirect('home')
    
    reserva = get_object_or_404(Reserva, pk=pk, agenda__prestador=request.user.perfil_prestador)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        reserva.estado = 'cancelada'
        reserva.fecha_cancelacion = timezone.now()
        reserva.motivo_cancelacion = motivo
        reserva.save()
        
        # Crear notificación para el cliente
        if reserva.cliente.usuario:
            Notificacion.objects.create(
                usuario=reserva.cliente.usuario,
                tipo='cancelacion',
                titulo='Reserva Cancelada',
                mensaje=f'Tu reserva del {reserva.fecha} ha sido cancelada. Motivo: {motivo}',
                reserva=reserva
            )
        
        messages.success(request, 'Reserva cancelada.')
        return redirect('reservas_list')
    
    return render(request, 'turnos/reserva_cancelar.html', {'reserva': reserva})

# ==================== VISTAS CLIENTE (PÚBLICO) ====================

def reserva_publica(request, slug):
    """Vista pública para hacer reservas"""
    prestador = get_object_or_404(PerfilPrestador, slug=slug, activo=True)
    servicios = prestador.servicios.filter(activo=True)
    agendas = prestador.agendas.filter(activa=True)
    
    context = {
        'prestador': prestador,
        'servicios': servicios,
        'agendas': agendas,
    }
    
    return render(request, 'turnos/reserva_publica.html', context)

def disponibilidad_ajax(request):
    """API para obtener horarios disponibles"""
    agenda_id = request.GET.get('agenda_id')
    fecha = request.GET.get('fecha')
    servicio_id = request.GET.get('servicio_id')
    
    if not all([agenda_id, fecha, servicio_id]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    agenda = get_object_or_404(Agenda, id=agenda_id)
    servicio = get_object_or_404(Servicio, id=servicio_id)
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    
    # Obtener reservas del día
    reservas = Reserva.objects.filter(
        agenda=agenda,
        fecha=fecha_obj,
        estado__in=['pendiente', 'confirmada']
    ).values_list('hora_inicio', 'hora_fin')
    
    # Generar slots disponibles
    slots = []
    hora_actual = agenda.hora_inicio
    duracion = timedelta(minutes=servicio.duracion_minutos)
    
    while hora_actual < agenda.hora_fin:
        hora_fin = (datetime.combine(fecha_obj, hora_actual) + duracion).time()
        
        if hora_fin <= agenda.hora_fin:
            # Verificar si el slot está ocupado
            ocupado = False
            for res_inicio, res_fin in reservas:
                if not (hora_fin <= res_inicio or hora_actual >= res_fin):
                    ocupado = True
                    break
            
            if not ocupado:
                slots.append(hora_actual.strftime('%H:%M'))
        
        hora_actual = (datetime.combine(fecha_obj, hora_actual) + timedelta(minutes=30)).time()
    
    return JsonResponse({'slots': slots})

def procesar_reserva(request):
    """Procesar nueva reserva"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    data = json.loads(request.body)
    
    # Obtener o crear cliente
    prestador = get_object_or_404(PerfilPrestador, id=data['prestador_id'])
    
    cliente, created = Cliente.objects.get_or_create(
        prestador=prestador,
        dni=data['dni'],
        defaults={
            'nombre': data['nombre'],
            'apellido': data['apellido'],
            'email': data['email'],
            'telefono': data.get('telefono', ''),
        }
    )
    
    # Verificar si está bloqueado
    if cliente.bloqueado:
        return JsonResponse({'error': 'Cliente bloqueado'}, status=403)
    
    # Crear reserva
    agenda = get_object_or_404(Agenda, id=data['agenda_id'])
    servicio = get_object_or_404(Servicio, id=data['servicio_id'])
    
    monto_total = servicio.precio
    monto_a_pagar = monto_total if prestador.requiere_pago_total else (monto_total * prestador.porcentaje_seña / 100)
    
    reserva = Reserva.objects.create(
        agenda=agenda,
        cliente=cliente,
        servicio=servicio,
        fecha=data['fecha'],
        hora_inicio=data['hora'],
        hora_fin=(datetime.combine(datetime.today(), datetime.strptime(data['hora'], '%H:%M').time()) + 
                  timedelta(minutes=servicio.duracion_minutos)).time(),
        monto_total=monto_total,
        estado='pendiente'
    )
    
    # Crear preferencia de MercadoPago
    if prestador.mp_access_token:
        sdk = mercadopago.SDK(prestador.mp_access_token)
        
        preference_data = {
            "items": [{
                "title": f"{servicio.nombre} - {prestador.nombre_negocio}",
                "quantity": 1,
                "unit_price": float(monto_a_pagar)
            }],
            "back_urls": {
                "success": f"{request.build_absolute_uri('/reserva/exito/')}?reserva={reserva.codigo}",
                "failure": f"{request.build_absolute_uri('/reserva/fallo/')}",
                "pending": f"{request.build_absolute_uri('/reserva/pendiente/')}"
            },
            "external_reference": str(reserva.codigo)
        }
        
        preference = sdk.preference().create(preference_data)
        reserva.mp_preference_id = preference["response"]["id"]
        reserva.save()
        
        return JsonResponse({
            'reserva_id': reserva.id,
            'mp_preference_id': preference["response"]["id"],
            'init_point': preference["response"]["init_point"]
        })
    
    return JsonResponse({'reserva_id': reserva.id})

def reserva_comprobante_pdf(request, codigo):
    """Generar comprobante PDF"""
    reserva = get_object_or_404(Reserva, codigo=codigo)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="comprobante_{codigo}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, f"Comprobante de Reserva")
    p.drawString(100, 730, f"Código: {reserva.codigo}")
    p.drawString(100, 710, f"Cliente: {reserva.cliente.nombre} {reserva.cliente.apellido}")
    p.drawString(100, 690, f"Servicio: {reserva.servicio.nombre}")
    p.drawString(100, 670, f"Fecha: {reserva.fecha}")
    p.drawString(100, 650, f"Hora: {reserva.hora_inicio}")
    p.drawString(100, 630, f"Monto: ${reserva.monto_pagado}")
    p.showPage()
    p.save()
    
    return response