from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify
from .models import Usuario, PerfilPrestador, Servicio, Agenda, Cliente, Reserva

class RegistroForm(UserCreationForm):
    """Formulario de registro para prestadores"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'correo@ejemplo.com'
    }))
    nombre_negocio = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre de tu negocio'
    }))
    slug = forms.SlugField(max_length=200, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'url-de-tu-negocio'
    }), help_text='Este será tu link único: turnos.com/tu-slug')
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'password1', 'password2', 'nombre_negocio', 'slug')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Usuario'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if PerfilPrestador.objects.filter(slug=slug).exists():
            raise forms.ValidationError('Este slug ya está en uso.')
        return slug

class PerfilPrestadorForm(forms.ModelForm):
    """Formulario para editar perfil de prestador"""
    class Meta:
        model = PerfilPrestador
        fields = [
            'nombre_negocio', 'descripcion', 'direccion', 'logo',
            'mp_access_token', 'mp_public_key', 
            'requiere_pago_total', 'porcentaje_seña',
            'horas_cancelacion_con_devolucion', 'horas_cancelacion_sin_devolucion'
        ]
        widgets = {
            'nombre_negocio': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'mp_access_token': forms.TextInput(attrs={'class': 'form-control'}),
            'mp_public_key': forms.TextInput(attrs={'class': 'form-control'}),
            'requiere_pago_total': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'porcentaje_seña': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'horas_cancelacion_con_devolucion': forms.NumberInput(attrs={'class': 'form-control'}),
            'horas_cancelacion_sin_devolucion': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nombre_negocio': 'Nombre del Negocio',
            'descripcion': 'Descripción',
            'direccion': 'Dirección',
            'logo': 'Logo',
            'mp_access_token': 'MercadoPago Access Token',
            'mp_public_key': 'MercadoPago Public Key',
            'requiere_pago_total': '¿Requiere pago total?',
            'porcentaje_seña': 'Porcentaje de seña (%)',
            'horas_cancelacion_con_devolucion': 'Horas para cancelar con devolución',
            'horas_cancelacion_sin_devolucion': 'Horas mínimas para cancelar',
        }

class ServicioForm(forms.ModelForm):
    """Formulario para crear/editar servicios"""
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'duracion_minutos', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Manicure completa'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control', 'step': '15'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre del Servicio',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio': 'Precio ($)',
            'duracion_minutos': 'Duración (minutos)',
            'activo': 'Activo',
        }

class AgendaForm(forms.ModelForm):
    """Formulario para crear/editar agendas"""
    class Meta:
        model = Agenda
        fields = [
            'nombre', 'descripcion', 'activa',
            'hora_inicio', 'hora_fin',
            'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'lunes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'martes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'miercoles': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'jueves': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'viernes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sabado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'domingo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClienteForm(forms.ModelForm):
    """Formulario para registrar clientes"""
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'email', 'dni', 'telefono', 'fecha_nacimiento', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReservaForm(forms.ModelForm):
    """Formulario para crear reservas (uso interno)"""
    class Meta:
        model = Reserva
        fields = ['agenda', 'cliente', 'servicio', 'fecha', 'hora_inicio', 'notas']
        widgets = {
            'agenda': forms.Select(attrs={'class': 'form-control'}),
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'servicio': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReservaPublicaForm(forms.Form):
    """Formulario para reservas públicas"""
    # Datos del cliente
    nombre = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre',
        'required': True
    }))
    apellido = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Apellido',
        'required': True
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'correo@ejemplo.com',
        'required': True
    }))
    dni = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'DNI',
        'required': True
    }))
    telefono = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Teléfono (opcional)'
    }))
    fecha_nacimiento = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date',
        'placeholder': 'Fecha de nacimiento (opcional)'
    }))
    
    # Datos de la reserva
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    agenda = forms.ModelChoiceField(
        queryset=Agenda.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    fecha = forms.DateField(widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date',
        'min': ''  # Se establecerá dinámicamente
    }))
    hora = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-control'}))
    
    def __init__(self, prestador=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if prestador:
            self.fields['servicio'].queryset = prestador.servicios.filter(activo=True)
            self.fields['agenda'].queryset = prestador.agendas.filter(activa=True)

class BusquedaClienteForm(forms.Form):
    """Formulario para buscar clientes"""
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, DNI o email...'
        })
    )

class FiltroReservasForm(forms.Form):
    """Formulario para filtrar reservas"""
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos')] + list(Reserva.ESTADOS),
        widget=forms.Select(attrs={'class': 'form-control'})
    )