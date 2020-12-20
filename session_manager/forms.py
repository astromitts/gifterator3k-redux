from django.conf import settings
from django.forms import (
    CharField,
    EmailField,
    EmailInput,
    Form,
    HiddenInput,
    ModelForm,
    PasswordInput,
    TextInput,
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from session_manager.models import SessionManager
from session_manager.utils import special_chars


def validate_unique_email(email, user_pk):
    return User.objects.filter(email=email).exclude(password='').exclude(pk=user_pk).count() == 0


def validate_email(clean_email, user_pk):
    error_message = None
    if not validate_unique_email(clean_email, user_pk):
        error_message = 'Invalid email: <ul><li>Email address already in use by another account.</li></ul>'
    return error_message


def validate_unique_username(username, user_pk):
    return User.objects.filter(username=username).exclude(pk=user_pk).count() == 0


def validate_username(clean_username, user_pk):
    username_errors = []
    error_message = None
    if len(clean_username) < 3:
        username_errors.append('<li>Must be at least 3 characters.</li>')

    username_invalid_char = False
    for char in clean_username:
        username_invalid_char = not char.isalpha() and not char.isnumeric() and char != '_'

    if username_invalid_char:
        username_errors.append(
            '<li>Letters, numbers, and underscores only, please.</li>'
        )

    username_is_unique = validate_unique_username(clean_username, user_pk)
    if not username_is_unique:
        username_errors.append(
            '<li>Username already in use.</li>'
        )

    if username_errors:
        error_message = 'Invalid username: <ul>{}</ul>'.format(''.join(username_errors))
    return error_message


def validate_password(clean_password, confirm_password):
    has_alpha = False
    has_number = False
    has_special = False
    password_errors = []
    error_message = None

    if len(clean_password) < 8:
        password_errors.append('<li>Must be at least 8 characters.</li>')

    for char in clean_password:
        if char.isalpha():
            has_alpha = True
        if char.isnumeric():
            has_number = True
        if char in special_chars:
            has_special = True
    if not has_alpha:
        password_errors.append('<li>Must contain at least one letter.</li>')
    if not has_number:
        password_errors.append('<li>Must contain at least one number.</li>')
    if not has_special:
        password_errors.append(
            '<li>Must contain at least one special character ({}).</li>'.format(
                ', '.join(special_chars)
            )
        )

    if confirm_password != clean_password:
        password_errors.append('<li>Password does not match.</li>')

    if password_errors:
        error_message = 'Invalid password: <ul>{}</ul>'.format(''.join(password_errors))
    return error_message


class CreateUserForm(ModelForm):
    confirm_password = CharField(widget=PasswordInput(attrs={'class': 'form-control'}))
    appuseruuid = CharField(widget=HiddenInput())

    def __init__(self, registration_type='website', *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)
        # self.fields['username'].help_text = 'Minimum 3 characters. Letters, numbers, and underscores only.'
        self.fields['password'].help_text = 'Minimum 8 characters. Must contain at least 1 letter, 1 number and 1 special character.'
        if registration_type == 'invitation':
            self.fields['email'].widget =  EmailInput(attrs={'class': 'form-control'})
        else:
            self.fields['email'].widget =  HiddenInput()

        if settings.MAKE_USERNAME_EMAIL:
            self.fields['username'].widget = HiddenInput()
        else:
            self.fields['username'].widget = TextInput(attrs={'class': 'form-control'})

    class Meta:
        model = User
        fields = [
                'email',
                'username',
                'first_name',
                'last_name',
                'password',
                'confirm_password',
                'appuseruuid',
            ]

        widgets = {
            'password': PasswordInput(attrs={'class': 'form-control'}),
            'first_name': TextInput(attrs={'class': 'form-control'}),
            'last_name': TextInput(attrs={'class': 'form-control'}),
            'appuseruuid': HiddenInput()
        }

    def clean(self):
        """ Enforces username and password requirements
        """
        super(CreateUserForm, self).clean()
        data = self.cleaned_data
        errors = []

        clean_password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        password_errors = validate_password(clean_password, confirm_password)
        if password_errors:
            errors.append(password_errors)

        clean_email = self.cleaned_data['email']
        email_error = validate_email(clean_email, 0)
        if email_error:
            errors.append(email_error)

        if errors:
            raise ValidationError(mark_safe('<br />'.join(errors)))
        return data


class ResetPasswordForm(ModelForm):
    user_id = CharField(widget=HiddenInput())
    confirm_password = CharField(widget=PasswordInput(attrs={'class': 'form-control'}))
    class Meta:
        model = User
        fields = ['password', 'confirm_password', 'user_id']
        widgets = {
            'password': PasswordInput(attrs={'class': 'form-control'}),
            'user_id': HiddenInput()
        }

    def clean(self):
        super(ResetPasswordForm, self).clean()
        data = self.cleaned_data
        user = User.objects.get(pk=data['user_id'])
        errors = []
        clean_password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        password_errors = validate_password(clean_password, confirm_password)
        if password_errors:
            errors.append(password_errors)

        if errors:
            raise ValidationError(mark_safe('<br />'.join(errors)))

        return data

class LoginEmailForm(ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': TextInput(attrs={'class': 'form-control'})
        }


class LoginPasswordForm(ModelForm):
    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
            'email': HiddenInput(),
            'password': PasswordInput(attrs={'class': 'form-control'})
        }


class RegistrationLinkForm(ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': HiddenInput(),
        }


class UserProfileForm(Form):
    def clean(self):
        super(UserProfileForm, self).clean()
        data = self.cleaned_data
        user = User.objects.get(pk=data['user_id'])
        errors = []

        if not settings.MAKE_USERNAME_EMAIL:
            clean_username = self.cleaned_data['username']
            username_errors = validate_username(clean_username, user.pk)
            if username_errors:
                errors.append(username_errors)

        clean_email = self.cleaned_data['email']
        email_error = validate_email(clean_email, user.pk)

        if email_error:
            errors.append(email_error)

        if errors:
            raise ValidationError(mark_safe(''.join(errors)))

        return data


class EmailForm(Form):
    email_address = CharField(widget=EmailInput(attrs={'class': 'form-control'}))


class UserProfileUsernameForm(UserProfileForm):
    user_id = CharField(widget=HiddenInput())
    email = EmailField(widget=EmailInput(attrs={'class': 'form-control'}))
    username = CharField(widget=TextInput(attrs={'class': 'form-control'}))
    first_name = CharField(widget=TextInput(attrs={'class': 'form-control'}))
    last_name = CharField(widget=TextInput(attrs={'class': 'form-control'}))

class UserProfileEmailUsernameForm(UserProfileForm):
    user_id = CharField(widget=HiddenInput())
    email = EmailField(widget=EmailInput(attrs={'class': 'form-control'}))
    first_name = CharField(widget=TextInput(attrs={'class': 'form-control'}))
    last_name = CharField(widget=TextInput(attrs={'class': 'form-control'}))
