import os
from celery import Celery
from celery.schedules import crontab

# Configurar Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_turnos.settings')

app = Celery('sistema_turnos')

# Configuración desde Django settings con namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en las apps instaladas
app.autodiscover_tasks()

# Configurar tareas periódicas
app.conf.beat_schedule = {
    # Enviar recordatorios diarios a las 18:00
    'enviar-recordatorios-diarios': {
        'task': 'turnos.tasks.enviar_recordatorios_diarios',
        'schedule': crontab(hour=18, minute=0),
    },
    
    # Marcar reservas no asistidas a las 00:00
    'marcar-no-asistidos': {
        'task': 'turnos.tasks.marcar_reservas_no_asistidas',
        'schedule': crontab(hour=0, minute=0),
    },
    
    # Limpiar notificaciones antiguas semanalmente (domingos a las 02:00)
    'limpiar-notificaciones': {
        'task': 'turnos.tasks.limpiar_notificaciones_antiguas',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },
    
    # Generar reportes diarios a las 08:00
    # Nota: Esta tarea se ejecutará para cada prestador activo
    'generar-reportes-diarios': {
        'task': 'turnos.tasks.generar_reportes_para_todos_prestadores',
        'schedule': crontab(hour=8, minute=0),
    },
}

@app.task(bind=True)
def debug_task(self):
    """Tarea de debug"""
    print(f'Request: {self.request!r}')