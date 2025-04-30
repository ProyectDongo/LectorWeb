from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, HuellaDigital, Asistencia,AudioPresentacion,Plan,Meta
from .forms import UsuarioForm

# Personalización para el modelo Usuario
class UsuarioAdmin(UserAdmin):
    model = Usuario
    form = UsuarioForm
    list_display = ('rut', 'first_name', 'last_name', 'telefono', 'plan', 'fecha_vencimiento', 'es_activo')
    list_filter = ('es_activo', 'plan')
    search_fields = ('rut', 'first_name', 'last_name')
    ordering = ('rut',)
    fieldsets = (
        (None, {'fields': ('rut', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'telefono', 'direccion')}),
        ('Membresía', {'fields': ('fecha_ingreso', 'plan', 'fecha_vencimiento', 'es_activo')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('rut', 'first_name', 'last_name', 'telefono', 'direccion', 'plan'),
        }),
    )

class AudioPresentacionAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'archivo')

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
admin.site.register(AudioPresentacion, AudioPresentacionAdmin)
admin.site.register(Plan)
admin.site.register(Meta)