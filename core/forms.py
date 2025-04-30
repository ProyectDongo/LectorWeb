from django import forms
from .models import Usuario, Plan

class UsuarioForm(forms.ModelForm):
    plan = forms.ModelChoiceField(queryset=Plan.objects.all(), required=True, label='Plan de Membresía')

    class Meta:
        model = Usuario
        fields = ['rut', 'first_name', 'last_name', 'telefono', 'direccion', 'plan']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345678-9',
                'pattern': '^[0-9]{7,8}-[0-9kK]{1}$'
            }),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rut'].label = 'RUT* (Formato: 12345678-9)'