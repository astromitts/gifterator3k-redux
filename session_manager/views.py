from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render, redirect, resolve_url
from django.template import loader
from django.views import View
from django.urls import reverse

from urllib.parse import urlparse

from session_manager.forms import (
    CreateUserForm,
    LoginEmailForm,
    LoginPasswordForm,
    RegistrationLinkForm,
    ResetPasswordForm,
    UserProfileUsernameForm,
    UserProfileEmailUsernameForm,
    validate_email,
)

from session_manager.mailer import SessionManagerEmailer
from session_manager.models import SessionManager, UserToken

class CreateUserView(View):
    """ Views for a new user registration
    """
    def setup(self, request, *args, **kwargs):
        super(CreateUserView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/register.html')
        self.context = {}

    def get(self, request, *args, **kwargs):
        if request.GET.get('token') and request.GET.get('user'):
            registration_token, token_error_message = UserToken.get_token(
                token=request.GET['token'],
                username=request.GET['user'],
                token_type='registration'
            )
            if not registration_token:
                messages.error(request, token_error_message)
                return redirect(reverse('session_manager_login'))
            elif not registration_token.is_valid:
                registration_token.delete()
                messages.error(request, 'Registration link invalid or expired')
                return redirect(reverse('session_manager_login'))
            else:
                if settings.MAKE_USERNAME_EMAIL:
                    initial = {
                        'email': registration_token.user.email,
                        'username': registration_token.user.username
                    }
                else:
                    initial = {
                        'email': registration_token.user.email,
                    }
                form = CreateUserForm(initial=initial)
        else:
            form = LoginEmailForm()
        self.context.update({
            'form': form,
        })
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        if 'password' in request.POST:
            form = CreateUserForm(request.POST)
            if form.is_valid():
                user = SessionManager.get_user_by_username(request.POST['email'])
                if not settings.MAKE_USERNAME_EMAIL:
                    username = request.POST['username']
                else:
                    username = request.POST['email']
                SessionManager.register_user(
                    user,
                    username=username,
                    password=request.POST['password'],
                    first_name=request.POST['first_name'],
                    last_name=request.POST['last_name']
                )
                messages.success(request, 'Registration complete! Please log in to continue.')
                UserToken.objects.filter(user=user, token_type='registration').all().delete()
                return redirect(reverse('session_manager_login'))
            else:
                self.context.update({
                    'form': form,
                })
                return HttpResponse(self.template.render(self.context, request))
        else:
            form = LoginEmailForm(request.POST)
            if form.is_valid():
                email_error = validate_email(request.POST['email'], 0)
                if email_error:
                    error = '{}<p>Did you mean to <a href="{}">log in instead</a>?'.format(
                        email_error, reverse('session_manager_login')
                    )
                    messages.error(request, error)
                else:
                    user = SessionManager.get_user_by_username(request.POST['email'])
                    if not user:
                        user = SessionManager.create_user(request.POST['email'])
                    UserToken.clean(user=user, token_type='registration')
                    token = UserToken(user=user, token_type='registration')
                    token._generate_token()
                    token.save()
                    mailer = SessionManagerEmailer()
                    mailer.send_app_registration_link(user, token)
                    if settings.PREVIEW_EMAILS_IN_APP:
                        self.context.update({'show_email': mailer})
                    messages.success(request, 'Thanks! To verify your email address, we have sent you a link to complete your registration.')
                    return HttpResponse(self.template.render(self.context, request))
            self.context.update({
                'form': form,
            })
            return HttpResponse(self.template.render(self.context, request))


class LoginUserView(View):
    """ Views for logging in an existing user, either via form post
        or token URL
    """
    def setup(self, request, *args, **kwargs):
        super(LoginUserView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/login.html')
        self.login_stage = 1
        self.context = {}

    def get(self, request, *args, **kwargs):
        # check if a login token was provided
        self.context.update({'login_stage': self.login_stage})
        if request.GET.get('token') and request.GET.get('user'):
            token, token_error_message = UserToken.get_token(token=request.GET['token'], username=request.GET['user'], token_type='login')
            if token:
                if token.is_valid:
                    # a valid token/user combination was given, so log in and delete the token
                    login(request, token.user)
                    token.delete()
                    request.session['user_is_authenticated'] = True
                    if settings.DISPLAY_AUTH_SUCCESS_MESSAGES:
                        messages.success(request, 'Log in successful.')
                    return redirect(reverse(settings.LOGIN_SUCCESS_REDIRECT))
                else:
                    # provided token was found, but it is expired
                    # clean up the token
                    token.delete()
                    messages.error(request, 'Token is expired.')
            else:
                # no matching token was found for provided user/token
                messages.error(request, token_error_message)

        # no token was provided, or it was invalid, so just render the login form
        form = LoginEmailForm()
        self.context.update({
            'form': form,
        })
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        # we should only get here if they submitted the form instead of a token in the URL
        # standard Django form handling here
        if 'password' not in request.POST:
            self.login_stage = 2
            self.context.update({'login_stage': self.login_stage})
            form = LoginEmailForm(request.POST)
            if form.is_valid():
                user = SessionManager.get_user_by_username_or_email(request.POST['email'])
                if not user:
                    messages.error(request, 'Could not find account with that email address.')
                elif not user.password:
                    messages.error(
                        request,
                        (
                            "It looks like you haven't completed your yet. "
                            "If your registration link was lost or is expired, you can "
                            "request a new one."
                        )
                    )
                    self.template = loader.get_template('session_manager/default.html')
                    self.context.update({
                        'form': RegistrationLinkForm(initial={'email': user.email}),
                        'submit_text': 'Re-send Registration Link',
                        'form_action': reverse('session_manager_send_registration_link'),
                        'email': user.email,
                    })
                    return HttpResponse(self.template.render(self.context, request))
                else:
                    self.context.update({
                        'form': LoginPasswordForm(initial={'email': user.email}),
                        'email': user.email,
                    })
                    return HttpResponse(self.template.render(self.context, request))
            else:
                messages.error(request, 'Something went wrong. Please correct errors below.')
                self.context.update({
                    'form': form,
                })
                return HttpResponse(self.template.render(self.context, request))
        else:
            self.login_stage = 3
            self.context.update({'login_stage': self.login_stage})
            form = LoginPasswordForm(request.POST)
            if form.is_valid():
                user, error_reason = SessionManager.check_user_login(
                    username_or_email=request.POST['email'],
                    password=request.POST['password']
                )
                if not user:
                    messages.error(request, error_reason)
                    self.context.update({
                        'form': form,
                    })
                    return HttpResponse(self.template.render(self.context, request))
                else:
                    login(request, user)
                    request.session['user_is_authenticated'] = True
                    if settings.DISPLAY_AUTH_SUCCESS_MESSAGES:
                        messages.success(request, 'Log in successful.')
                    return redirect(reverse(settings.LOGIN_SUCCESS_REDIRECT))
        return HttpResponse(self.template.render(self.context, request))


class SendRegistrationLink(View):
    def post(self, request, *args, **kwargs):
        context = {}
        form = RegistrationLinkForm(request.POST)
        if form.is_valid():
            user = SessionManager.get_user_by_username(request.POST['email'])
            UserToken.clean(
                token_type='registration',
                user=user
            )
            registration_token = UserToken(
                token_type='registration',
                user=user
            )
            registration_token._generate_token()
            registration_token.save()
            mailer = SessionManagerEmailer()
            mailer.send_app_registration_link(user, registration_token)
            messages.success(
                request,
                'A registration link was sent to {}. Use the provided link to complete registration.'.format(registration_token.user.email)
            )
            template = loader.get_template('session_manager/default.html')
            if settings.PREVIEW_EMAILS_IN_APP:
                context.update({'show_email': mailer})
            return HttpResponse(template.render(context, request))
        else:
            messages.error(request, 'Could not validate request.')
            return redirect(reverse('session_manager_login'))


class SendPasswordResetLink(View):
    def post(self, request, *args, **kwargs):
        template = loader.get_template('session_manager/default.html')
        context = {}
        form = LoginEmailForm(request.POST)
        if form.is_valid():
            user = SessionManager.get_user_by_username(request.POST['email'])
            UserToken.clean(
                token_type='reset',
                user=user
            )
            reset_token = UserToken(
                token_type='reset',
                user=user
            )
            reset_token._generate_token()
            reset_token.save()
            mailer = SessionManagerEmailer()
            mailer.send_password_reset_link(reset_token)
            messages.success(
                request,
                'A password reset link was sent to {}. You have 48 hours to use it.'.format(reset_token.user.email)
            )
            if settings.PREVIEW_EMAILS_IN_APP:
                context.update({'show_email': mailer})
        else:
            messages.error(request, 'Could not validate request.')
        return HttpResponse(template.render(context, request))


class ResetPasswordWithTokenView(View):
    """ View that allows a user to reset their password via a token,
        without needing to log in
    """
    def setup(self, request, *args, **kwargs):
        super(ResetPasswordWithTokenView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/reset_password.html')
        self.context = {}
        # get the token and error message, needed for both GET and POST
        self.token, self.token_error_message = UserToken.get_token(
            token=request.GET.get('token'),
            username=request.GET.get('user'),
            token_type='reset'
        )

    def get(self, request, *args, **kwargs):
        # If we find a valid token, show the reset form with the user's ID passed to it
        if self.token:
            if self.token.is_valid:
                form = ResetPasswordForm(initial={'user_id': self.token.user.id})
                self.context.update({'form': form})
            else:
                messages.error(request, 'Token is expired.')
        else:
            messages.error(request, self.token_error_message)
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = ResetPasswordForm(request.POST)
        # if a valid token was given and the form is valid, reset user's password
        # and redirect to login
        if self.token:
            if self.token.is_valid:
                if form.is_valid():
                    user = SessionManager.get_user_by_id(request.POST['user_id'])
                    user.set_password(request.POST['password'])
                    user.save()
                    messages.success(request, 'Password reset. Please log in to continue.')
                    self.token.delete()
                    return redirect(reverse('session_manager_login'))
            else:
                messages.error(request, 'Token is expired.')
        else:
            messages.error(request, self.token_error_message)
        self.context.update({'form': form})
        return HttpResponse(self.template.render(self.context, request))


class ResetPasswordFromProfileView(View):
    """ View that allows a user to reset their password when logged in
    """
    def setup(self, request, *args, **kwargs):
        super(ResetPasswordFromProfileView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/reset_password.html')
        self.context = {
            'breadcrumbs': [
                ('Profile', reverse('session_manager_profile')),
                ('Reset Password', None)
            ]
        }

    def get(self, request, *args, **kwargs):
        form = ResetPasswordForm(initial={'user_id': self.request.user.id})
        self.context.update({'form': form})
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user = User.objects.get(pk=request.POST['user_id'])
            user.set_password(request.POST['password'])
            user.save()
            messages.success(request, 'Your password has been reset. Please log in again to continue.')
            return redirect(reverse(settings.PW_RESET_SUCCESS_REDIRECT))
        self.context.update({'form': form})
        return HttpResponse(self.template.render(self.context, request))


class LogOutUserView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'Logged out.')
        request.session['user_is_authenticated'] = False
        return redirect(reverse('session_manager_login'))


class Profile(View):
    def get(self, request, *args, **kwargs):
        template = loader.get_template('session_manager/profile.html')
        context = {
            'show_username': not settings.MAKE_USERNAME_EMAIL
        }
        return HttpResponse(template.render(context, request))


class UpdateProfileView(View):
    def setup(self, request, *args, **kwargs):
        super(UpdateProfileView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/default.html')
        if settings.MAKE_USERNAME_EMAIL:
            self.form = UserProfileEmailUsernameForm
        else:
            self.form = UserProfileUsernameForm

    def get(self, request, *args, **kwargs):
        initial = {
            'email': self.request.user.email,
            'first_name': self.request.user.first_name,
            'last_name': self.request.user.last_name,
            'user_id': self.request.user.pk,
        }
        if not settings.MAKE_USERNAME_EMAIL:
            initial['username'] = self.request.user.username

        form = self.form(initial=initial)
        context = {
            'form': form,
        }
        return HttpResponse(self.template.render(context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            # django doesn't like to update request.user directly as this is a lazy load object
            user = User.objects.get(pk=self.request.user.pk)

            if settings.MAKE_USERNAME_EMAIL:
                user.username = request.POST['email']
            else:
                user.username = request.POST['username']

            user.email = request.POST['email']
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.save()
            messages.success(request, 'Profile updated.')
            return redirect(reverse('session_manager_profile'))
        else:
            context = {
                'form': form,
            }
            return HttpResponse(self.template.render(context, request))
