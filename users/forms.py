from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
    
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        
        # Custom validation: ít nhất 4 ký tự (thay vì 8)
        if len(password1) < 4:
            raise ValidationError("Mật khẩu phải có ít nhất 4 ký tự.")
        
        return password1
