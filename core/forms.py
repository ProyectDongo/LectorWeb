from django import forms
from .models import Usuario

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['rut', 'first_name', 'last_name', 'telefono', 'direccion', 'modo_pago']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678-9',
                'pattern': '^[0-9]{7,8}-[0-9kK]{1}$'
            }),
            'modo_pago': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 12
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rut'].label = 'RUT* (Formato: 12345678-9)'
        self.fields['modo_pago'].label = 'Duración Membresía (meses)*'