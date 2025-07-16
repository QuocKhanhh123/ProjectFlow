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

class ProfileUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên đăng nhập'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tên'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Họ'
            })
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Only check for uniqueness if email is actually changed
        if email != self.instance.email:
            if User.objects.filter(email=email).exists():
                raise ValidationError("Email này đã được sử dụng.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Only check for uniqueness if username is actually changed
        if username != self.instance.username:
            if User.objects.filter(username=username).exists():
                raise ValidationError("Tên đăng nhập này đã được sử dụng.")
        return username

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu hiện tại'
        })
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mật khẩu mới'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Xác nhận mật khẩu mới'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("Mật khẩu hiện tại không đúng.")
        return old_password
    
    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')
        if len(new_password1) < 4:
            raise ValidationError("Mật khẩu mới phải có ít nhất 4 ký tự.")
        return new_password1
    
    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError("Mật khẩu mới và xác nhận mật khẩu không khớp.")
        return new_password2
    
    def save(self):
        new_password = self.cleaned_data['new_password1']
        self.user.set_password(new_password)
        self.user.save()
        return self.user
