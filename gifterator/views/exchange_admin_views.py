from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse
from django.template import loader
from django.utils import timezone
from django.utils.html import strip_tags

from gifterator.forms import (
    GiftExchangeBaseForm,
    ParticipantEmailForm,
    InvitationEmailForm,
    SendMessageForm,
)
from gifterator.mailer import GifteratorMailer
from gifterator.models import (
    ExchangeAssignment,
    GiftExchange,
    ExchangeParticipant,
    AppUser,
)
from gifterator.views.base_views import GifteratorBase
from session_manager.models import SessionManager, UserToken


class GiftExchangeAdminEmailer(GifteratorBase):
    def get(self, request, *args, **kwargs):
        self.template = loader.get_template('session_manager/default.html')
        mail_type = kwargs.get('mail_type')
        if mail_type == 'send-assignment':
            assignment = ExchangeAssignment.objects.get(pk=request.GET['assignment_id'])
            mailer = GifteratorMailer()
            mailer.send_assignment_email(assignment)
        elif mail_type == 'exchange-invitation':
            invitee = ExchangeParticipant.objects.get(pk=request.GET['participant_id'])
            mailer = GifteratorMailer()
            mailer.send_exchange_invitation_email(invitee.appuser, self.giftexchange, existing_user=True)

        if settings.PREVIEW_EMAILS_IN_APP:
            self.context.update({'show_email': mailer})
        return HttpResponse(self.template.render(self.context, request))


class GiftExchangeAdminAppInvite(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(GiftExchangeAdminAppInvite, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('gifterator/giftexchange_manage_invite_user.html')
        self.form = InvitationEmailForm
        self.context.update({
            'breadcrumbs': [
                ('Gift Exchanges', reverse('gifterator_dashboard')),
                (
                    '{} Admin'.format(self.giftexchange.title),
                    reverse('gifterator_exchange_admin_dashboard', kwargs={'ex_uuid': self.giftexchange.uuid})
                ),
                ('Invite new user', None)
            ]
        })

    def get(self, request, *args, **kwargs):
        self.context.update({'form': self.form()})
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            user_exists = SessionManager.get_user_by_username_or_email(strip_tags(request.POST['email']))
            if user_exists:
                messages.error(request, '{} already has an account.'.format(user_exists.email))
            else:
                new_app_user = AppUser()
                new_app_user.save()
                participant = ExchangeParticipant.get_or_create(
                    appuser=new_app_user,
                    giftexchange=self.giftexchange,
                    status='pending'
                )
                UserToken.clean(appuser=new_app_user, token_type='invitation')
                token = UserToken(appuser=new_app_user, token_type='invitation')
                token._generate_token()
                token.save()
                mailer = GifteratorMailer()
                mailer.send_exchange_invitation_email(
                    request.POST['email'],
                    self.giftexchange,
                    existing_user=False,
                    registration_token=token
                )

                messages.success(request, 'An invitation has been sent to {}!'.format(request.POST['email']))
                if settings.PREVIEW_EMAILS_IN_APP:
                    self.context.update({'show_email': mailer})
        self.context.update({'form': self.form()})
        return HttpResponse(self.template.render(self.context, request))


class GiftExchangeAdminDashboard(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(GiftExchangeAdminDashboard, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('gifterator/giftexchange_manage_dashboard.html')
        self.context.update({
            'PREVIEW_EMAILS_IN_APP': settings.PREVIEW_EMAILS_IN_APP,
            'breadcrumbs': [
                ('Gift Exchanges', reverse('gifterator_dashboard')),
                ('{} Admin'.format(self.giftexchange.title), None),
            ],
            'send_message_form': SendMessageForm()
        })
        self.exchange_details_form = GiftExchangeBaseForm
        self.participant_email_form = ParticipantEmailForm
        self.non_model_initial = {
                'created_by_pk': self.giftexchange.created_by.pk,
                'giftexchange_pk': self.giftexchange.pk,
            }
        exchange_details_form = self.exchange_details_form(
            giftexchange=self.giftexchange,
            non_model_initial=self.non_model_initial
        )
        participant_email_form = self.participant_email_form
        self.context['pending_count'] = self.giftexchange.exchangeparticipant_set.filter(status='pending').count()
        self.context['exchange_details_form'] = exchange_details_form
        self.context['participant_email_form'] = participant_email_form
        self.return_url = reverse(
            'gifterator_exchange_admin_dashboard',
            kwargs={'ex_uuid': self.giftexchange.uuid}
        )

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.template.render(self.context, request))


class GiftExchangeAdminDashboardApi(GiftExchangeAdminDashboard):
    def setup(self, request, *args, **kwargs):
        super(GiftExchangeAdminDashboardApi, self).setup(request, *args, **kwargs)
        self.data = {
            'giftExchange': {
                'locked': self.giftexchange.locked,
                'participantCount': self.participant_list.count(),
                'hasAssignments': self.assigment_list.count() > 0,
                'participantsNotified': self.giftexchange.participants_notified,
            }
        }
        self.participant_email_form = ParticipantEmailForm

    def _refresh_data(self):
        self.data['giftExchange'].update({
            'locked': self.giftexchange.locked,
            'participantCount': self.participant_list.count(),
            'hasAssignments': self.assigment_list.count() > 0,
            'participantsNotified': self.giftexchange.participants_notified,
        })

    def _render_participant_list(self, request):
        result_html = loader.render_to_string(
            'gifterator/admin_dashboard_includes/participant_list.html',
            context=self.context,
            request=request
        )
        return {
            'status': 'success',
            'html': result_html
        }

    def _get_participant_subset(self, subset_target):
        if subset_target == 'all':
            participant_subset = self.giftexchange.exchangeparticipant_set.filter(
                appuser__user__isnull=False).all()
        elif subset_target == 'active':
            participant_subset = self.giftexchange.exchangeparticipant_set.filter(status='active').all()
        elif subset_target == 'invited':
            participant_subset = self.giftexchange.exchangeparticipant_set.filter(
                status='invited', appuser__user__isnull=False).all()
        return participant_subset

    def get(self, request, *args, **kwargs):
        return JsonResponse(self.data)

    def post(self, request, *args, **kwargs):
        post_target = request.POST.get('js_target')
        self.data.update({'postTarget': post_target})
        if post_target == 'email-search':
            search_results = SessionManager.search(strip_tags(request.POST['email']))
            valid_results = []
            for user in search_results.all():
                if user not in self.active_participant_users:
                    valid_results.append(user)
            self.context.update({
                'search_results': valid_results,
                'search_term': request.POST['email']
            })
            result_html = loader.render_to_string(
                'gifterator/admin_dashboard_includes/search_results.html',
                context=self.context,
                request=request
            )
            self.data.update({
                'status': 'success',
                'html': result_html
            })
        elif post_target == 'add-user':
            user = SessionManager.get_user_by_username_or_email(strip_tags(request.POST['user-email']))
            if user == self.user:
                self.participant.status = 'active'
                self.participant.save()
            else:
                # TODO get_or_create here?
                participant = ExchangeParticipant.get_or_create(
                    appuser=user.appuser,
                    status='invited',
                    giftexchange=self.giftexchange
                )
            email_view_url = '{}?participant_id={}'.format(
                reverse(
                    'gifterator_exchange_admin_sendmail',
                    kwargs={
                        'ex_uuid': self.giftexchange.uuid,
                        'mail_type': 'exchange-invitation'
                    }
                ),
                participant.pk
            )
            self.data.update(self._render_participant_list(request))
            self.data.update({'postProcessUrl': email_view_url})
        elif post_target == 'remove-user':
            user = SessionManager.get_user_by_username_or_email(request.POST['user-email'])
            participant = ExchangeParticipant.objects.get(appuser__user=user, giftexchange=self.giftexchange)
            if user == self.user:
                participant.status = 'inactive'
                participant.save()
            else:
                participant.delete()
            self.data.update(self._render_participant_list(request))
        elif post_target == 'update-details':
            exchange_details_form = self.exchange_details_form(
                self.giftexchange,
                self.non_model_initial,
                request.POST,
            )
            if exchange_details_form.is_valid():
                post_data = {field: strip_tags(str(value)) for field, value in request.POST.items()}
                for field in GiftExchange.boolean_fields():
                    if post_data.get(field) == 'on':
                        post_data[field] = True
                    else:
                        post_data[field] = False
                self.giftexchange.update(**post_data)
                self.data.update({
                    'status': 'success',
                    'message': 'Updated gift exchange details'
                })
            else:
                error_messages = []
                for field, message_list in exchange_details_form.errors.items():
                    error_messages.append('<strong>{}</strong><br /> {}'.format(
                        field, '<br />'.join(message_list)
                    ))
                self.data.update({
                    'status': 'error',
                    'message': '<br />'.join(error_messages)
                })
        elif post_target == 'set-assignments':
            self.giftexchange.generate_assignemnts(override_lock=False)
            self.context.update({
                'assignment_list': self.giftexchange.exchangeassignment_set.all()
            })
            result_html = loader.render_to_string(
                'gifterator/admin_dashboard_includes/assignments_list.html',
                context=self.context,
                request=request,
            )
            self.data.update({
                'status': 'success',
                'html': result_html
            })
        elif post_target == 'lock-assignments':
            self.giftexchange.locked = True
            self.giftexchange.save()
            self.data.update({
                'status': 'success',
            })
        elif post_target == 'unset-assignments':
            self.giftexchange.locked = False
            self.assigment_list.all().delete()
            self.giftexchange.save()
            self.data.update(self._render_participant_list(request))
        elif post_target == 'notify-participants':
            self.giftexchange.participants_notified = True
            self.giftexchange.save()
            for assignment in self.giftexchange.exchangeassignment_set.all():
                mailer = GifteratorMailer()
                mailer.send_assignment_email(assignment)
                assignment.giver.email_last_sent = timezone.now()
                assignment.giver.save()
            result_html = loader.render_to_string(
                'gifterator/admin_dashboard_includes/assignments_list.html',
                context=self.context,
                request=request,
            )
            self.data.update({
                'status': 'success',
                'html': result_html
            })

        elif post_target == 'notify-single-participant':
            assignment = ExchangeAssignment.objects.get(pk=request.POST['assignment_id'])
            mailer = GifteratorMailer()
            mailer.send_assignment_email(assignment)
            assignment.giver.email_last_sent = timezone.now()
            assignment.giver.save()
            result_html = loader.render_to_string(
                'gifterator/admin_dashboard_includes/assignments_list.html',
                context=self.context,
                request=request,
            )
            self.data.update({
                'status': 'success',
                'html': result_html
            })
        elif post_target == 'send-bulk-message':
            message_target = request.POST['target']
            message_body = strip_tags(request.POST['message'])
            target_users = self._get_participant_subset(message_target)
            mailer = GifteratorMailer()
            mailer.send_admin_message(
                giftexchange_name=self.giftexchange.title,
                message_body=message_body,
                from_user=self.participant,
                to_users=target_users
            )
            self.data.update({
                'status': 'success',
                'successMessage': 'Sent an email to {} users'.format(target_users.count()),
                'html': None,
            })

        self._refresh_data()
        return JsonResponse(self.data)
