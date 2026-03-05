from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Profile

User = get_user_model()


class MyUserCreationForm(UserCreationForm):
   
    first_name = forms.CharField(required=False, max_length=30, label="First name")
    last_name = forms.CharField(required=False, max_length=150, label="Last name")
    email = forms.EmailField(required=True, label="Email")
    roll_no = forms.CharField(required=False, max_length=50, label="Roll No")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "roll_no", "password1", "password2")

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError("Email is required.")

        qs = User.objects.filter(email__iexact=email)
        
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(is_active=True).exists():
            raise ValidationError("This email is already registered. Try logging in or resetting your password.")
        if qs.filter(is_active=False).exists():
            raise ValidationError(
                "An account with this email exists but is not activated. "
                "Please check your email for the activation link or use password reset / contact support."
            )
        return email

    def clean_roll_no(self):
        roll_no = (self.cleaned_data.get('roll_no') or '').strip()
        if roll_no:
            qs = Profile.objects.filter(roll_no__iexact=roll_no)
           
            if self.instance and self.instance.pk:
                qs = qs.exclude(user_id=self.instance.pk)
            if qs.exists():
                raise ValidationError("This roll number is already in use.")
        return roll_no

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = (self.cleaned_data.get('email') or '').strip().lower()

        if commit:
            user.save()
            
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.roll_no = self.cleaned_data.get('roll_no', '')
            profile.save()
        else:
            
            user._pending_roll_no = self.cleaned_data.get('roll_no', '')
        return user