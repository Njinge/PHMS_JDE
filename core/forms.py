from django import forms
import re
from django.utils.html import escape

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        # Password policy enforcement
        if password:
            errors = []
            if len(password) < 8:
                errors.append('Password must be at least 8 characters long.')
            if not re.search(r'[A-Z]', password):
                errors.append('Password must contain at least one uppercase letter.')
            if not re.search(r'[a-z]', password):
                errors.append('Password must contain at least one lowercase letter.')
            if not re.search(r'\d', password):
                errors.append('Password must contain at least one digit.')
            if not re.search(r'[^A-Za-z0-9]', password):
                errors.append('Password must contain at least one special character.')
            if username and username.lower() in password.lower():
                errors.append('Password is too similar to the username.')
            if email and email.split('@')[0].lower() in password.lower():
                errors.append('Password is too similar to the email address.')
            if errors:
                self.add_error('password', ' '.join(errors))
        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    ROLE_CHOICES = [
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)

class PatientProfileForm(forms.Form):
    full_name = forms.CharField(max_length=255, required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    address = forms.CharField(max_length=255, required=True)
    phone = forms.CharField(max_length=50, required=True)

class MedicalRecordForm(forms.Form):
    diagnosis = forms.CharField(widget=forms.Textarea, required=True)
    treatment = forms.CharField(widget=forms.Textarea, required=True)
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=True)

    def clean(self):
        cleaned_data = super().clean()
        if 'diagnosis' in cleaned_data:
            cleaned_data['diagnosis'] = escape(cleaned_data['diagnosis'])
        if 'treatment' in cleaned_data:
            cleaned_data['treatment'] = escape(cleaned_data['treatment'])
        return cleaned_data

class LabResultForm(forms.Form):
    test_name = forms.CharField(max_length=255, required=True)
    result = forms.CharField(widget=forms.Textarea, required=True)
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=True)

class PrescriptionForm(forms.Form):
    medication = forms.CharField(max_length=255, required=True)
    dosage = forms.CharField(max_length=255, required=True)
    instructions = forms.CharField(widget=forms.Textarea, required=True)
    date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=True)

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, required=True)
    new_password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_new_password = forms.CharField(widget=forms.PasswordInput, required=True)

    def __init__(self, *args, **kwargs):
        self.username = kwargs.pop('username', None)
        self.email = kwargs.pop('email', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')
        if new_password and confirm_new_password and new_password != confirm_new_password:
            self.add_error('confirm_new_password', 'New passwords do not match.')
        # Password policy enforcement
        if new_password:
            errors = []
            if len(new_password) < 8:
                errors.append('Password must be at least 8 characters long.')
            if not re.search(r'[A-Z]', new_password):
                errors.append('Password must contain at least one uppercase letter.')
            if not re.search(r'[a-z]', new_password):
                errors.append('Password must contain at least one lowercase letter.')
            if not re.search(r'\d', new_password):
                errors.append('Password must contain at least one digit.')
            if not re.search(r'[^A-Za-z0-9]', new_password):
                errors.append('Password must contain at least one special character.')
            if self.username and self.username.lower() in new_password.lower():
                errors.append('Password is too similar to the username.')
            if self.email and self.email.split('@')[0].lower() in new_password.lower():
                errors.append('Password is too similar to the email address.')
            if errors:
                self.add_error('new_password', ' '.join(errors))
        return cleaned_data

# If file uploads are added, use FileField with validators for file type and size.
# Example:
# from django.core.validators import FileExtensionValidator
# file = forms.FileField(validators=[FileExtensionValidator(['pdf', 'jpg', 'png'])], required=False)
# In clean_file, check file.size and file.content_type. 