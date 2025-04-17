from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, HuellaDigital, Asistencia
from .forms import UsuarioForm

# Personalización para el modelo Usuario
class UsuarioAdmin(UserAdmin):
    model = Usuario
    form = UsuarioForm
    list_display = ('rut', 'first_name', 'last_name', 'telefono', 'direccion', 'fecha_ingreso', 'modo_pago', 'fecha_vencimiento', 'es_activo')
    list_filter = ('es_activo', 'modo_pago', 'fecha_vencimiento')
    search_fields = ('rut', 'first_name', 'last_name')
    ordering = ('rut',)
    fieldsets = (
        (None, {'fields': ('rut', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'telefono', 'direccion')}),
        ('Membresía', {'fields': ('fecha_ingreso', 'modo_pago', 'fecha_vencimiento', 'es_activo')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('rut', 'first_name', 'last_name', 'password1', 'password2', 'telefono', 'direccion', 'modo_pago'),
        }),
    )

# Personalización para el modelo HuellaDigital
class HuellaDigitalAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_registro', 'calidad')
    search_fields = ('usuario__rut', 'usuario__first_name', 'usuario__last_name')
    readonly_fields = ('fecha_registro', 'template')
    list_filter = ('calidad',)

# Personalización para el modelo Asistencia
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'fecha_hora', 'tipo')
    list_filter = ('tipo', 'fecha_hora')
    search_fields = ('usuario__rut', 'usuario__first_name', 'usuario__last_name')
    ordering = ('-fecha_hora',)

# Registro de los modelos en el admin
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(HuellaDigital, HuellaDigitalAdmin)
admin.site.register(Asistencia, AsistenciaAdmin)