from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from session_manager.models import UserToken
from session_manager.utils import TimeDiff

from bs4 import BeautifulSoup
from datetime import datetime, timedelta


class SessionManagerTestCase(TestCase):
    """ Base class for SessionManager Test Cases
    """

    def setUp(self, *args, **kwargs):
        super(SessionManagerTestCase, self).setUp(*args, **kwargs)
        self.register_url = reverse('session_manager_register')
        self.login_url = reverse('session_manager_login')
        self.password_reset_url = reverse('session_manager_profile_reset_password')

    def assertMessageInContext(self, request, message_text):
        """ Helper function to raise an assertion error if an expected message
            is absent from request context
        """
        messages = [msg.message for msg in request.context['messages']._loaded_messages]
        self.assertIn(message_text, messages)

    def assertNonFieldFormError(self, request, message_text):
        """ Helper function to raise an assertion error if an expected message
            is absent from the rendered request HTML
        """
        content = BeautifulSoup(request.content, features="html.parser")
        error_list = content.find('ul', {'class': 'errorlist nonfield'})
        self.assertIn(message_text, error_list.text)

    def _create_user(self, username_or_email, username=None, password=None, confirm_password=None):
        """ Helper function to make a user and return it
        """
        user = User(email=username_or_email)
        if username:
            user.username=username
        else:
            user.username=username_or_email
        user.save()
        if password:
            user.set_password(password)
            user.save()
        return user

    def _login_user(self, post_data, follow=True):
        if 'username_or_email' in post_data and 'email' not in post_data:
            post_data['email'] = post_data['username_or_email']
        return self.client.post(self.login_url, post_data, follow=follow)


class MiddlewareTestCase(SessionManagerTestCase):
    def test_middleware_404(self):
        with self.settings(MIDDLEWARE_DEBUG=False):
            bad_url = '/asdf/'
            result_request = self.client.get(bad_url)
            self.assertEqual(result_request.status_code, 404)

    def test_middleware_authentication_not_required(self):
        with self.settings(MIDDLEWARE_DEBUG=False):
            bad_url = '/login/'
            result_request = self.client.get(bad_url)
            self.assertEqual(result_request.status_code, 200)

    def test_middleware_authentication_required(self):
        with self.settings(MIDDLEWARE_DEBUG=False):
            profile_url = reverse('session_manager_profile')
            result_request = self.client.get(profile_url, follow=True)
            self.assertMessageInContext(
                result_request,
                'You must be authenticated to access this page. Please log in.'
            )

    def test_authenticated_user_passes_middelware(self):
        user_data = {
            'username_or_email': 'test@example.com',
            'username': 'tester',
            'password': 't3st3r@dmin'
        }
        user = self._create_user(**user_data)
        self._login_user(user_data)
        profile_url = reverse('session_manager_profile')
        with self.settings(MIDDLEWARE_DEBUG=False):
            result_request = self.client.get(profile_url, follow=True)
            self.assertEqual(
                result_request.request['PATH_INFO'],
                profile_url
            )
            self.assertEqual(result_request.status_code, 200)


class TestRegistrationFlow(SessionManagerTestCase):
    """ Test cases for form based registration
    """
    def test_register_user_happy_path_no_username(self):
        """ Verify a user can register when they provide all the correct data settings.MAKE_USERNAME_EMAIL = True
        """

        with self.settings(MAKE_USERNAME_EMAIL=True):
            register_get = self.client.get(self.register_url)
            self.assertEqual(register_get.status_code, 200)

            post_data_page_1 = {
                'email': 'test@example.com',
            }
            post_data_page_2 = {
                'email': 'test@example.com',
                'username': 'test-user',
                'first_name': 'Bo',
                'last_name': 'Morin',
                'password': 't3st3r@dmin',
                'confirm_password': 't3st3r@dmin',
            }

            register_page_1 = self.client.post(self.register_url, post_data_page_1, follow=True)
            self.assertMessageInContext(register_page_1, 'Thanks! To verify your email address, we have sent you a link to complete your registration.')

            register_page_2 = self.client.post(self.register_url, post_data_page_2, follow=True)
            self.assertMessageInContext(register_page_2, 'Registration complete! Please log in to continue.')

            new_user = User.objects.get(email=post_data_page_2['email'])
            self.assertEqual(new_user.username, post_data_page_2['email'])
            self.assertTrue(new_user.check_password(post_data_page_2['password']))

    def test_register_user_happy_path_with_username(self):
        """ Verify a user can register when they provide all the correct data with settings.MAKE_USERNAME_EMAIL = False
        """

        with self.settings(MAKE_USERNAME_EMAIL=False):
            register_get = self.client.get(self.register_url)
            self.assertEqual(register_get.status_code, 200)

            post_data_page_1 = {
                'email': 'test@example.com',
            }
            post_data_page_2 = {
                'email': 'test@example.com',
                'username': 'test-user',
                'first_name': 'Bo',
                'last_name': 'Morin',
                'password': 't3st3r@dmin',
                'confirm_password': 't3st3r@dmin',
            }

            register_page_1 = self.client.post(self.register_url, post_data_page_1, follow=True)
            self.assertMessageInContext(register_page_1, 'Thanks! To verify your email address, we have sent you a link to complete your registration.')

            register_page_2 = self.client.post(self.register_url, post_data_page_2, follow=True)
            self.assertMessageInContext(register_page_2, 'Registration complete! Please log in to continue.')

            new_user = User.objects.get(email=post_data_page_2['email'])
            self.assertEqual(new_user.username, post_data_page_2['username'])
            self.assertTrue(new_user.check_password(post_data_page_2['password']))

    def test_email_already_exists(self):
        """ Verify the correct registration error message when a email already exists
        """
        existing_user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin',
            'confirm_password': 't3st3r@dmin',
        }
        self._create_user(**existing_user_data)

        post_data = {
            'email': existing_user_data['username_or_email'],
        }

        register_post = self.client.post(self.register_url, post_data)
        self.assertMessageInContext(register_post, 'Invalid email: <ul><li>Email address already in use by another account.</li></ul><p>Did you mean to <a href="/login/">log in instead</a>?')

    def test_password_requirements(self):
        """ Verify the correct registration error message when a username already exists
        """
        must_contain_letter = 'Must contain at least one letter.'
        must_contain_number = 'Must contain at least one number.'
        must_contain_special = 'Must contain at least one special character'
        min_length = 'Must be at least 8 characters.'
        confirm_password = 'Password does not match.'

        bad_password_posts = [
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': 't1$',
                    'confirm_password': 't1$',
                },
                'expected_errors': [min_length, ]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': 'tt$',
                    'confirm_password': 'tt$',
                },
                'expected_errors': [min_length, must_contain_number]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': 'tt1',
                    'confirm_password': 'tt1',
                },
                'expected_errors': [min_length, must_contain_special]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': '$$1',
                    'confirm_password': '$$1',
                },
                'expected_errors': [min_length, must_contain_letter]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': 'tttttttt',
                    'confirm_password': 'v',
                },
                'expected_errors': [must_contain_special, must_contain_number]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': '1111111111',
                    'confirm_password': '1111111111',
                },
                'expected_errors': [must_contain_special, must_contain_letter]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': '##########',
                    'confirm_password': '##########',
                },
                'expected_errors': [must_contain_number, must_contain_letter]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': '#########1',
                    'confirm_password': '#########1',
                },
                'expected_errors': [must_contain_letter]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': '#########a',
                    'confirm_password': '#########a',
                },
                'expected_errors': [must_contain_number]
            },
            {
                'post_data': {
                    'email': 'different@example.com',
                    'username': 'tester',
                    'password': '111###aaa',
                    'confirm_password': '111###aab',
                },
                'expected_errors': [confirm_password]
            },
        ]

        for post in bad_password_posts:
            register_post = self.client.post(self.register_url, post['post_data'])
            for expected_error in post['expected_errors']:
                self.assertNonFieldFormError(register_post, expected_error)


class TestLoginFlow(SessionManagerTestCase):
    """ Test cases for form based log in
    """
    def test_login_happy_path(self):
        """ Verify a user can log in with the correct email and password
        """
        with self.settings(DISPLAY_AUTH_SUCCESS_MESSAGES=True):
            post_data = {
                'username_or_email': 'test@example.com',
                'password': 't3st3r@dmin'
            }
            self._create_user(**post_data)
            login_request = self._login_user(post_data)
            self.assertEqual(login_request.status_code, 200)

            self.assertMessageInContext(login_request, 'Log in successful.')

    def test_login_no_user(self):
        """ Verify correct log in error message when given email does not exist
        """
        post_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin'
        }
        login_request = self._login_user(post_data)
        self.assertEqual(login_request.status_code, 200)
        self.assertMessageInContext(login_request, 'User matching email does not exist.')

    def test_login_badpassword(self):
        """ Verify correct log in error message when bad password given
        """
        post_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin'
        }
        self._create_user(**post_data)
        post_data['password'] = 'badpassword'
        login_request = self._login_user(post_data)
        self.assertEqual(login_request.status_code, 200)
        self.assertMessageInContext(login_request, 'Password incorrect.')


class TestResetPasswordFromProfile(SessionManagerTestCase):
    """ Test cases for resetting password from user profile when logged in
    """
    def test_password_reset(self):
        """ Verify reset password from profile link
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin',
            'confirm_password': 't3st3r@dmin',
        }
        user = self._create_user(**user_data)
        self._login_user(user_data)
        new_password = 't3st3r@dminnewpass'
        reset_request = self.client.post(
            self.password_reset_url,
            {
                'user_id': user.pk,
                'password': new_password,
                'confirm_password': new_password,
            },
            follow=True
        )
        self.assertMessageInContext(reset_request, 'Your password has been reset. Please log in again to continue.')


class TestTokenLogin(SessionManagerTestCase):
    """ Test cases for token based log in
    """
    def test_login_with_token_happy_path(self):
        """ Verify log in with token when valid token and username given in URL
        """

        with self.settings(DISPLAY_AUTH_SUCCESS_MESSAGES=True):
            user_data = {
                'username_or_email': 'test@example.com',
                'password': 't3st3r@dmin'
            }
            user = self._create_user(**user_data)
            user_token = UserToken(user=user, token_type='login')
            user_token.save()
            token_str = user_token.token
            login_request = self.client.get(user_token.path, follow=True)
            self.assertMessageInContext(login_request, 'Log in successful.')
            user_token = UserToken.objects.filter(token=token_str)
            self.assertFalse(user_token.exists())

    def test_login_with_token_user_not_found(self):
        """ Verify correct log in token error message when bad username given in URL
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin'
        }
        user = self._create_user(**user_data)
        user_token = UserToken(user=user, token_type='login')
        user_token.save()
        login_request = self.client.get(user_token.path.replace(user_token.user.username, 'asdf'), follow=True)
        self.assertMessageInContext(login_request, 'User matching username not found.')

    def test_login_with_token_not_found(self):
        """ Verify correct log in token error message when bad token given in URL
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin'
        }
        user = self._create_user(**user_data)
        user_token = UserToken(user=user, token_type='login')
        user_token.save()
        login_request = self.client.get(user_token.path.replace(user_token.token, 'asdf'), follow=True)
        self.assertMessageInContext(login_request, 'Token not found.')

    def test_login_with_token_expired(self):
        """ Verify correct log in token error message when expired token given in URL
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin'
        }
        user = self._create_user(**user_data)
        user_token = UserToken(user=user, token_type='login', expiration=TimeDiff.yesterday())
        user_token.save()
        login_request = self.client.get(user_token.path, follow=True)
        self.assertMessageInContext(login_request, 'Token is expired.')


class TestTokenPasswordReset(SessionManagerTestCase):
    """ Test cases for token based password reset
    """
    def test_password_reset_happy_path(self):
        """ Verify password reset with correct token and user works
        """
        with self.settings(DISPLAY_AUTH_SUCCESS_MESSAGES=True):
            user_data = {
                'username_or_email': 'test@example.com',
                'username': 'testuser',
                'password': 't3st3r@dmin'
            }
            user = self._create_user(**user_data)
            user_token = UserToken(user=user, token_type='reset')
            user_token.save()
            reset_request = self.client.get(user_token.path, follow=True)
            self.assertIn('form', str(reset_request.content))
            post_data = {
                'user_id': user.pk,
                'password': 't3st3r@dminnewpass',
                'confirm_password': 't3st3r@dminnewpass'
            }
            reset_request = self.client.post(user_token.path, post_data, follow=True)
            self.assertMessageInContext(reset_request, 'Password reset. Please log in to continue.')
            user_data = {
                'username_or_email': 'test@example.com',
                'password': post_data['password']
            }
            login_request = self._login_user(user_data)
            self.assertMessageInContext(login_request, 'Log in successful.')

    def test_password_reset_bad_token(self):
        """ Verify correct error token password reset error message with bad token
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin',
            'username': 'testuser',
        }
        user = self._create_user(**user_data)
        user_token = UserToken(user=user, token_type='reset')
        user_token.save()
        reset_request = self.client.get(user_token.path.replace(user_token.token, 'asdf'), follow=True)
        self.assertMessageInContext(reset_request, 'Token not found.')

    def test_password_reset_bad_user(self):
        """ Verify correct error token password reset error message with bad user
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'username': 'testuser',
            'password': 't3st3r@dmin'
        }
        user = self._create_user(**user_data)
        user_token = UserToken(user=user, token_type='reset')
        user_token.save()
        reset_request = self.client.get(user_token.path, follow=True)
        self.assertIn('form', str(reset_request.content))
        post_data = {
            'user_id': user.pk,
            'password': 't3st3r@dminnewpass',
        }
        reset_request = self.client.get(user_token.path.replace(user_token.user.username, 'asdf'), post_data, follow=True)
        self.assertMessageInContext(reset_request, 'User matching username not found.')

    def test_password_reset_expired(self):
        """ Verify correct error token password reset error message with expired token
        """
        user_data = {
            'username_or_email': 'test@example.com',
            'password': 't3st3r@dmin',
            'username': 'testuser',
        }
        user = self._create_user(**user_data)
        user_token = UserToken(user=user, token_type='reset', expiration=TimeDiff.yesterday())
        user_token.save()
        reset_request = self.client.get(user_token.path, follow=True)
        self.assertMessageInContext(reset_request, 'Token is expired.')
