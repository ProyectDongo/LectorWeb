from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from .models import HuellaDigital

class FingerprintBackend(BaseBackend):
    def authenticate(self, request, fingerprint=None, **kwargs):
        try:
            huella = HuellaDigital.objects.filter(template=fingerprint).first()
            if huella:
                return huella.usuario
            return None
        except Exception as e:
            return None

    def get_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
