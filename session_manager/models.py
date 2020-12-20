from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from django.urls import reverse

from datetime import datetime, timedelta

import hashlib
import pytz
import random
import string
import uuid

from session_manager.utils import TimeDiff


class SessionManager(models.Model):
    """ Abstract helper model for login, register and log out
    """
    class Meta:
        abstract = True

    @classmethod
    def user_exists(cls, email):
        """ Return True/False if User with given email exists
        """
        user_qs = User.objects.filter(email=email)
        return user_qs.exists()

    @classmethod
    def get_user_by_username(cls, username):
        """ Retrieve User if one with a matching username exists
        """
        return User.objects.filter(username__iexact=username).first()

    @classmethod
    def get_user_by_username_or_email(cls, username_or_email):
        """ Retrieve User if one with a matching username exists
        """
        if '@' in username_or_email:
            user = User.objects.filter(email__iexact=username_or_email).first()
        else:
            user = User.objects.filter(username__iexact=username_or_email).first()
        return user

    @classmethod
    def search(cls, email):
        """ Retrieve User if one with a matching email exists
        """
        return User.objects.filter(email__icontains=email).all()

    @classmethod
    def full_search(cls, search_term):
        """ Retrieve User if one with a matching username exists
        """
        filter_qs = User.objects
        if '@' in search_term:
            filter_qs = filter_qs.filter(email__icontains=search_term)
        elif ' ' in search_term:
            search_names = search_term.split(' ')
            first_name = search_names[0]
            last_name = ' '.join(search_names[1:])
            filter_qs = filter_qs.filter(
                Q(first_name__icontains=first_name)|
                Q(last_name__icontains=last_name)
            )
        else:
            filter_qs = filter_qs.filter(
                Q(first_name__icontains=search_term)|
                Q(last_name__icontains=search_term)
            )
        return filter_qs.all()

    @classmethod
    def get_user_by_id(cls, pk):
        """ Get the User of given primary key
        """
        return User.objects.get(pk=pk)

    @classmethod
    def preregister_email(cls, email):
        """ Creates a User instance from the first registration form
            We don't ask for username until they have verified their
            email address by clicking the complete registration link
            in the email that gets sent from the pre-register page.
            So, put their email address as their username for now.
        """
        new_user = User(email=email, username=email)
        new_user.save()
        appuser = AppUser(user=new_user, registration_source='website')
        appuser.save()
        return new_user, appuser

    @classmethod
    def create_appuser(cls):
        appuser = AppUser()
        appuser.save()
        return appuser

    @classmethod
    def register_user(cls, user, first_name=' ', last_name=' ', password=None,  username=None):
        """ Create a new User instance, set the password and return the User object
        """
        if not username:
            user.username = user.email
        else:
            user.username = username
        user.first_name = first_name
        user.last_name = last_name

        user.save()
        if password:
            user.set_password(password)
            user.save()
        return user

    @classmethod
    def create_user(cls, email, first_name=' ', last_name=' ', password=None,  username=None):
        """ Create a new User instance, set the password and return the User object
        """
        if not username:
            username = email
        new_user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        new_user.save()
        if password:
            new_user.set_password(password)
            new_user.save()
        return new_user

    @classmethod
    def check_user_login(cls, username_or_email, password):
        """ Checks password for given email and password combination if the email has a User
            Returns tuple
                (
                    object: User if it is found and the password is correct,
                    string: error message if user not found or password incorrect
                )
        """
        if '@' in username_or_email:
            user = User.objects.filter(email__iexact=username_or_email).first()
        else:
            user = User.objects.filter(username__iexact=username_or_email).first()
        if not user:
            return (None, 'User matching email does not exist.')
        if not user.password:
            return (None, 'User needs to set password.')
        else:
            if user.check_password(password):
                return (user, None)
            else:
                return (None, 'Password incorrect.')


class AppUser(models.Model):
    user = models.OneToOneField(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    uuid = models.UUIDField(default=uuid.uuid4)
    registration_source = models.CharField(
        max_length=25,
        choices=(
            ('website', 'website'),
            ('invitation', 'invitation')
        )
    )
    post_process_status = models.CharField(
        max_length=50,
        choices=(
            ('invitation processed', 'invitation processed'),
            ('not processed', 'not processed'),
            ('registration processed', 'registration processed')
        ),
        default='not processed',
    )

    def __str__(self):
        return '{} AppUser: {} [{}] post process: {}'.format(
            self.status,
            self.pk,
            self.email,
            self.post_process_status
        )

    @property
    def status(self):
        if not self.user:
            return 'Unregistered'
        if self.user and not self.user.password:
            return 'Pregistered'
        if self.user and self.user.password:
            return 'Registered'

    @property
    def last_name(self):
        if self.user:
            return self.user.last_name
        return ''

    @property
    def first_name(self):
        if self.user:
            return self.user.first_name
        return ''

    @property
    def full_name(self):
        if self.user:
            return self.user.get_full_name()
        return ''

    @property
    def email(self):
        if self.user:
            return self.user.email
        return ''

    @property
    def username(self):
        if self.user:
            return self.user.username
        return ''

    def post_process_registration(self, registration_type, user):
        if registration_type == 'website':
            self.post_process_status = 'registration processed'
        elif registration_type == 'invitation':
            self.post_process_status = 'invitation processed'
        self.user = user
        self.save()
        for invite in self.exchangeparticipant_set.all():
            invite.status = 'invited'
            invite.save()


class UserToken(models.Model):
    """ Model for generating tokens that be used to login users without
        password or for resetting passwords
    """
    appuser = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, blank=True)
    token_type = models.CharField(
        max_length=20,
        choices=(
            ('reset', 'reset'),
            ('login', 'login'),
            ('registration', 'registration'),
            ('invitation', 'invitation'),
        )
    )
    expiration = models.DateTimeField(blank=True, default=TimeDiff.fourtyeighthoursfromnow)

    @classmethod
    def clean(cls, appuser, token_type):
        cls.objects.filter(appuser=appuser, token_type=token_type).all().delete()

    def _generate_token(self):
        """ Helper function to generate unique tokens
        """
        token_base = '{}-{}-{}'.format(
            self.appuser.uuid,
            datetime.now(),
            ''.join(random.choices(string.ascii_uppercase + string.digits, k = 60))
        )
        token_hash = hashlib.sha256(token_base.encode())
        return token_hash.hexdigest()

    def save(self, *args, **kwargs):
        """ Override the save function so that a token is generated on initial creation
        """
        if not self.token:
            self.token = self._generate_token()
        super(UserToken, self).save(*args, **kwargs)

    @property
    def path(self):
        """ Get the URL path expected by the login and password reset views
        """
        token_params = 'token={}&id={}'.format(
            self.token,
            self.appuser.uuid
        )
        if self.token_type == 'login':
            return '{}?{}'.format(reverse('session_manager_login'), token_params)
        elif self.token_type in ['registration', 'invitation']:
            return '{}?{}'.format(reverse('session_manager_register'), token_params)
        elif self.token_type == 'reset':
            return '{}?{}'.format(reverse('session_manager_token_reset_password'), token_params)

    @property
    def link(self):
        """ Get a full link for the path based on the HOST value found in settings
        """
        return '{}{}'.format(settings.HOST, self.path)

    def __str__(self):
        return 'UserToken: {} // AppUser: {} // type: {} // expires: {}'.format(self.pk, self.appuser, self.token_type, self.expiration)

    @classmethod
    def get_token(cls, token, appuser, token_type):
        """ Retrieve a token that matches the given username and type if it exists
            Returns a tuple:
                (object: UserToken if found, string: error message if no token found)
        """
        if isinstance(token_type, list):
            token = cls.objects.filter(
                appuser=appuser,
                token=token,
                token_type__in=token_type
            ).first()
        else:
            token = cls.objects.filter(
                appuser=appuser,
                token=token,
                token_type=token_type
            ).first()
        if not token:
            return (None, 'Token not found.')
        else:
            return (token, None)

    @property
    def is_valid(self):
        """ Returns True if the token is not expired, else returns False
        """
        utc=pytz.UTC
        if self.expiration >= utc.localize(datetime.now()):
            return True
        else:
            return False


class EmailLog(models.Model):
    email_type = models.CharField(max_length=50)
    to_email = models.EmailField()
    from_email = models.EmailField()
    subject = models.CharField(max_length=300)
    body = models.TextField()

    def __str__(self):
        return '<EmailLog {}: type "{}" to "{}">'.format(
            self.pk,
            self.email_type,
            self.to_email
        )
