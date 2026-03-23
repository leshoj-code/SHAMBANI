from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Equipment, UserProfile


class EquipmentForm(forms.ModelForm):
    class Meta:
        model   = Equipment
        fields  = ['name', 'type', 'price_per_hour', 'location']
        widgets = {
            'location': forms.HiddenInput(),
        }


class SignupForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. John Kamau'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'e.g. john@email.com'})
    )
    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 0712345678'})
    )
    role = forms.ChoiceField(
        choices=[('owner', 'Equipment Owner'), ('renter', 'Farmer / Renter')],
        widget=forms.RadioSelect
    )

    class Meta:
        model  = User
        fields = ['username', 'full_name', 'email', 'phone', 'role', 'password1', 'password2']