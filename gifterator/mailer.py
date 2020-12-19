from django.conf import settings
from session_manager.mailer import SessionManagerEmailer
from django.template.loader import render_to_string


class GifteratorMailer(SessionManagerEmailer):
    def send_assignment_email(self, exchange_assignment):
        to_email = exchange_assignment.giver.user.email
        email_type ='Assignment email'
        subject = 'You have been given an assignment for "{}"!'.format(
            exchange_assignment.giftexchange.title
        )
        self.context.update({
            'reciever': exchange_assignment.reciever
        })
        html_body = render_to_string(
            'gifterator/emails/assignment_email.html',
            context=self.context,
        )
        self.send_email(
            email_type,
            to_email,
            subject,
            html_body
        )

    def send_exchange_invitation_email(self, participant, giftexchange, existing_user=True, registration_token=None):
        if existing_user:
            to_email = participant.user.email
        else:
            to_email = participant
        email_type ='Exchange invitation email'
        subject = 'You have been invited to participate in a gift exchange!'
        self.context.update({
            'giftexchange': giftexchange,
            'host': settings.HOST,
            'existing_user': existing_user,
            'token': registration_token
        })
        html_body = render_to_string(
            'gifterator/emails/participant_invitation.html',
            context=self.context,
        )
        self.send_email(
            email_type,
            to_email,
            subject,
            html_body
        )
