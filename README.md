# Sistema de Turnos Automatizado

Sistema de gestión de turnos para negocios locales y emprendedores. Permite gestionar servicios, agendas, clientes y reservas con pagos integrados mediante MercadoPago.

## 🚀 Características Principales

### Para Prestadores de Servicios
- ✅ Registro y login con Google
- ✅ Panel de control completo
- ✅ Gestión de múltiples servicios (precios, duración, categorías)
- ✅ Múltiples agendas para equipos de trabajo
- ✅ Ficha completa de clientes con historial
- ✅ Sistema de blacklist para clientes
- ✅ Políticas de cancelación configurables
- ✅ Integración con MercadoPago
- ✅ Notificaciones automáticas
- ✅ Reportes y estadísticas

### Para Clientes
- ✅ Reserva sencilla mediante link único
- ✅ Registro rápido o reserva como invitado
- ✅ Selección de servicios y horarios disponibles
- ✅ Pago online (total o seña)
- ✅ Comprobante en PDF descargable
- ✅ Notificaciones por email

## 📋 Requisitos Previos

- Python 3.10 o superior
- PostgreSQL 13 o superior
- Redis (para tareas asíncronas)
- Cuenta de MercadoPago (para pagos)
- Cuenta de Google Cloud (para autenticación)

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/BelDelgado/sistema-turnos.git
cd sistema-turnos
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

```bash
# Crear base de datos
sudo -u postgres psql
CREATE DATABASE turnos_db;
CREATE USER turnos_user WITH PASSWORD 'tu_password';
ALTER ROLE turnos_user SET client_encoding TO 'utf8';
ALTER ROLE turnos_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE turnos_user SET timezone TO 'America/Argentina/Buenos_Aires';
GRANT ALL PRIVILEGES ON DATABASE turnos_db TO turnos_user;
\q
```

### 5. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Django
SECRET_KEY=tu-secret-key-super-secreta
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=turnos_db
DB_USER=turnos_user
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-aplicacion
DEFAULT_FROM_EMAIL=noreply@turnos.com

# Google OAuth2
GOOGLE_OAUTH2_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=tu-client-secret
GOOGLE_OAUTH2_REDIRECT_URI=http://localhost:8000/auth/google/callback

# MercadoPago
MERCADOPAGO_PUBLIC_KEY=tu-public-key
MERCADOPAGO_ACCESS_TOKEN=tu-access-token

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 6. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Crear superusuario

```bash
python manage.py createsuperuser
```

### 8. Recolectar archivos estáticos

```bash
python manage.py collectstatic
```

### 9. Iniciar servidor de desarrollo

```bash
python manage.py runserver
```

### 10. Iniciar Celery (en otra terminal)

```bash
celery -A sistema_turnos worker -l info
celery -A sistema_turnos beat -l info
```

## 🔑 Configuración de Integraciones

### Google OAuth2

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un nuevo proyecto
3. Habilitar Google+ API
4. Crear credenciales OAuth 2.0
5. Agregar URIs de redirección autorizadas:
   - http://localhost:8000/auth/google/callback
   - https://tu-dominio.com/auth/google/callback
6. Copiar Client ID y Client Secret al archivo .env

### MercadoPago

1. Crear cuenta en [MercadoPago Developers](https://www.mercadopago.com.ar/developers/)
2. Ir a "Tus aplicaciones"
3. Crear nueva aplicación
4. Obtener credenciales de prueba:
   - Public Key
   - Access Token
5. Para producción, usar credenciales de producción
6. Configurar URLs de notificación (webhooks)

## 📁 Estructura del Proyecto

```
sistema-turnos/
├── manage.py
├── requirements.txt
├── .env
├── sistema_turnos/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── celery.py
├── turnos/
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   ├── urls.py
│   ├── tasks.py
│   ├── migrations/
│   └── templates/
│       └── turnos/
│           ├── base.html
│           ├── home.html
│           ├── dashboard_prestador.html
│           ├── reserva_publica.html
│           └── ...
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── media/
    └── logos/
```

## 🎯 Uso del Sistema

### Como Prestador

1. **Registro**: Acceder a `/registro/` y crear cuenta
2. **Configurar Perfil**: Completar datos del negocio y configurar MercadoPago
3. **Crear Servicios**: Agregar servicios con precios y duración
4. **Configurar Agenda**: Definir horarios y días laborables
5. **Compartir Link**: Compartir tu link único con clientes (ej: `/reservar/mi-negocio/`)

### Como Cliente

1. **Acceder al Link**: Ingresar al link del prestador
2. **Completar Datos**: Nombre, apellido, DNI, email
3. **Seleccionar Servicio**: Elegir servicio y fecha/hora
4. **Pagar**: Realizar pago online
5. **Descargar Comprobante**: Guardar comprobante en PDF

## 🚀 Deploy en Render

### 1. Preparar el proyecto

Crear archivo `render.yaml`:

```yaml
databases:
  - name: turnos-db
    databaseName: turnos_db
    user: turnos_user

services:
  - type: web
    name: sistema-turnos
    env: python
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --no-input
      python manage.py migrate
    startCommand: gunicorn sistema_turnos.wsgi:application
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
      - key: DATABASE_URL
        fromDatabase:
          name: turnos-db
          property: connectionString
```

### 2. Configurar en Render

1. Crear cuenta en [Render](https://render.com/)
2. Conectar repositorio de GitHub
3. Crear Web Service desde dashboard
4. Configurar variables de entorno
5. Deploy automático

## 📊 Modelos de Datos

### Usuario
- Extendido de AbstractUser
- Roles: admin, prestador, cliente
- Integración con Google

### PerfilPrestador
- Datos del negocio
- Configuración de pagos
- Políticas de cancelación
- Link único (slug)

### Servicio
- Nombre y descripción
- Precio y duración
- Categoría
- Estado activo/inactivo

### Agenda
- Horarios de atención
- Días laborables
- Múltiples agendas por prestador

### Cliente
- Datos personales
- Historial de servicios
- Blacklist

### Reserva
- Estado (pendiente, confirmada, cancelada, completada)
- Datos de pago
- Integración con MercadoPago

## 🔒 Seguridad

- Autenticación requerida para vistas sensibles
- CSRF protection
- SQL injection prevention (ORM de Django)
- XSS protection
- HTTPS en producción
- Variables de entorno para datos sensibles

## 📧 Notificaciones

El sistema envía notificaciones automáticas para:
- Nueva reserva (prestador)
- Confirmación de reserva (cliente)
- Recordatorio 24hs antes (cliente)
- Cancelación de turno (ambos)
- Pago recibido (prestador)

## 🐛 Troubleshooting

### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
sudo service postgresql status
sudo service postgresql start
```

### Error con Celery
```bash
# Verificar que Redis esté corriendo
sudo service redis-server status
sudo service redis-server start
```

### Errores con archivos estáticos
```bash
python manage.py collectstatic --clear
python manage.py collectstatic
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Licencia

Este proyecto es de código abierto y gratuito para la comunidad.

## 👨‍💻 Autor

Desarrollado para ayudar a negocios locales y emprendedores a digitalizar su gestión de turnos.

## 📞 Soporte

Para consultas o problemas, abrir un issue en GitHub.

---

**¡Gracias por usar Sistema de Turnos! 🎉**