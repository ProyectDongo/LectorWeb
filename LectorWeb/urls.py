"""
URL configuration for LectorWeb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from core import views



urlpatterns = [
    path("admin/", admin.site.urls),
    
    path("", views.home, name='home'),


    path('registrar_usuario/', views.registrar_usuario, name='registrar_usuario'),
    path('registro_huella/<int:user_id>/', views.registro_huella, name='registro_huella'),
    path('api/registro_huella/<int:user_id>/', views.FingerprintRegistrationView.as_view(), name='api_registro_huella'),
    

    path('lecto_ingreso/', views.lecto_ingreso, name='lecto_ingreso'),
    path('verificar_huella/', views.verificar_huella, name='verificar_huella'),
    path('registrar_asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('editar_usuario/<int:user_id>/', views.editar_usuario, name='editar_usuario'),



    path('eliminar_usuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('actualizar_membresia/<int:user_id>/', views.actualizar_membresia, name='actualizar_membresia'),
]

