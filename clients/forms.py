from django import forms
from .models import Client

class ClientForm(forms.ModelForm):
    class Meta:
        model  = Client
        fields = ['nom', 'email', 'telephone', 'adresse']
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }
