from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(required=True,label='First Name')
    last_name = forms.CharField(required=True,label='Last Name')

    email = forms.EmailField(required=True, label='Email')
    termsAndConditions = forms.BooleanField(required=True)


    class Meta:
        model = User
        fields = ("first_name","last_name","username", "email", "password1", "password2")
        
    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user