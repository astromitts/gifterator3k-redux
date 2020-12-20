from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from session_manager.models import EmailLog
from django.template.loader import render_to_string

from session_manager.context_processors import session_manager_app_context


class SessionManagerEmailer(object):
    to_email = None
    subject = None
    html_body = None

    def __init__(self):
        # Because we are doing render_to_string to print emails, instead of
        # rendering a template through a view request, the django context
        # processors are not called. Call the app contex processor manually here.
        self.context = session_manager_app_context()

        self.context.update({
            'reply_to': settings.EMAIL_REPLY_TO,
        })

    def send_email(self, email_type, to_email, subject, html_body):
        self.to_email = to_email
        self.subject = subject
        self.html_body = html_body
        self.email_type = email_type
        self.from_email = settings.EMAILS_FROM

        if settings.LOG_EMAILS:
            email_log = EmailLog(
                email_type=email_type,
                to_email=to_email,
                from_email=settings.EMAILS_FROM,
                subject=subject,
                body=html_body
            )
            email_log.save()

        if settings.SEND_EMAILS and settings.SENDGRID_API_KEY and not to_email.endswith('@example.com'):
            message = Mail(
                from_email=settings.EMAILS_FROM,
                to_emails=to_email,
                subject=subject,
                html_content=html_body
            )
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            return response

    def _send_app_registration_link(self, subject, email_type, to_email, token):
        self.context.update({
            'token': token,
            'host': settings.HOST
        })
        body = render_to_string(
            'session_manager/emails/registration_link.html',
            context=self.context,
        )
        self.send_email(
            email_type,
            to_email,
            subject,
            body
        )

    def send_app_registration_link(self, to_user, token):
        email_type = 'Self Registration'
        subject = 'Your registration link has arrived!'
        to_email = to_user.email
        self._send_app_registration_link(subject, email_type, to_email, token)

    def send_app_invitation_link(self, to_user, from_user, organization, token):
        email_type = 'App Invitation From User'
        to_email = to_user.email
        subject = '{} {} has invited you to join {}'.format(
            from_user.first_name, from_user.last_name, settings.APP_NAME
        )
        self._send_app_registration_link(subject, email_type, to_email, token)

    def send_password_reset_link(self, token):
        self.context.update({
            'token': token,
            'host': settings.HOST
        })

        to_email = token.user.email
        email_type = 'Password Reset Link'
        subject = '{} Password Reset Link'.format(settings.APP_NAME)
        body = render_to_string(
            'session_manager/emails/password_reset_link.html',
            context=self.context,
        )
        self.send_email(
            email_type,
            to_email,
            subject,
            body
        )
