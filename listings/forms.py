from django import forms
from .models import Equipment

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['name', 'type', 'price_per_hour', 'location']
        widgets = {
            # We hide the location input because the user interacts with the Map, not a text box
            'location': forms.HiddenInput(), 
        }