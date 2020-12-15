from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from django.urls import reverse

from datetime import datetime, timedelta
import pytz

import hashlib
import random
import string

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


class UserToken(models.Model):
    """ Model for generating tokens that be used to login users without
        password or for resetting passwords
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, blank=True)
    token_type = models.CharField(
        max_length=20,
        choices=(
            ('reset', 'reset'),
            ('login', 'login'),
            ('registration', 'registration'),

        )
    )
    expiration = models.DateTimeField(blank=True, default=TimeDiff.fourtyeighthoursfromnow)

    @classmethod
    def clean(cls, user, token_type):
        cls.objects.filter(user=user, token_type=token_type).all().delete()

    def _generate_token(self):
        """ Helper function to generate unique tokens
        """
        token_base = '{}-{}-{}'.format(
            self.user.email,
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
        if self.token_type == 'login':
            return '{}?token={}&user={}'.format(reverse('session_manager_login'), self.token, self.user.username)
        elif self.token_type == 'registration':
            return '{}?token={}&user={}'.format(reverse('session_manager_register'), self.token, self.user.username)
        else:
            return '{}?token={}&user={}'.format(reverse('session_manager_token_reset_password'), self.token, self.user.username)

    @property
    def link(self):
        """ Get a full link for the path based on the HOST value found in settings
        """
        return '{}{}'.format(settings.HOST, self.path)

    def __str__(self):
        return 'UserToken Object: {} // User: {} // type: {} // expires: {}'.format(self.pk, self.user.email, self.token_type, self.expiration)

    @classmethod
    def get_token(cls, token, username, token_type):
        """ Retrieve a token that matches the given username and type if it exists
            Returns a tuple:
                (object: UserToken if found, string: error message if no token found)
        """
        user = SessionManager.get_user_by_username(username)
        if not user:
            return (None, 'User matching username not found.')
        token = cls.objects.filter(user=user, token=token, token_type=token_type).first()
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
