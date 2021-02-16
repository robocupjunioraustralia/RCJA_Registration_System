from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput

class CustomAuthForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={'class':'validate','placeholder': 'Email Address', 'autofocus': True}))
    password = forms.CharField(strip=False, widget=PasswordInput(attrs={'placeholder':'Password', 'autocomplete': 'current-password'}))
