from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, resolve_url
from django.template import loader
from django.views import View
from django.urls import reverse

from gifterator.forms import (
    GiftExchangeBaseForm,
    GiftExchangeCreateForm,
    ParticipantDetailsForm,
    ParticipantEmailForm,
    InvitationEmailForm,
    UserDefaultForm,
)
from gifterator.mailer import GifteratorMailer
from gifterator.models import (
    ExchangeAssignment,
    GiftExchange,
    ExchangeParticipant,
    AppUser,
)
from session_manager.models import SessionManager, UserToken


class GifteratorBase(View):
    def setup(self, request, *args, **kwargs):
        super(GifteratorBase, self).setup(request, *args, **kwargs)
        self.user = self.request.user
        self.appuser = AppUser.objects.get(user=self.user)
        self.context = {
            'breadcrumbs': []
        }
        if 'ex_uuid' in kwargs:
            self.giftexchange = GiftExchange.objects.get(uuid=kwargs['ex_uuid'])
            self.participant = ExchangeParticipant.objects.get(
                appuser=self.appuser,
                giftexchange=self.giftexchange
            )
            self.participant_list = self.giftexchange.exchangeparticipant_set.filter(status='active')
            self.active_participant_users = [
                p.appuser.user for p in self.participant_list
            ]
            self.all_participant_users = [
                p.appuser.user for p in self.giftexchange.exchangeparticipant_set.all()
            ]
            self.invited_list = self.giftexchange.exchangeparticipant_set.filter(status='invited')
            self.assigment_list = self.giftexchange.exchangeassignment_set
            self.context.update({
                'user': self.user,
                'appuser': self.appuser,
                'giftexchange': self.giftexchange,
                'participant': self.participant,
                'participant_list': self.participant_list,
                'invited_list': self.invited_list,
                'assignment_list': self.assigment_list
            })

class UserDefaultManager(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(UserDefaultManager, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/default.html')
        self.form = UserDefaultForm
        self.context['breadcrumbs'] = [
            ('Profile', reverse('session_manager_profile')),
            ('Default Exchange Settings', None)
        ]
        self.return_url = reverse('session_manager_profile')

    def get(self, request, *args, **kwargs):
        form = self.form(instance=self.appuser.userdefault)
        self.context.update({'form': form})
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            post_data = {field: str(value) for field, value in request.POST.items()}
            self.appuser.userdefault.update(**post_data)
            messages.success(request, 'Updated your default goft exchange settings')
            return redirect(self.return_url)
        self.context.update({'form': form})
        return HttpResponse(self.template.render(self.context, request))


class GiftExchangeDashboard(GifteratorBase):
    def get(self, request, *args, **kwargs):
        template = loader.get_template('gifterator/dashboard.html')
        admin_exchange_participants = ExchangeParticipant.objects.filter(appuser=self.appuser, is_admin=True)
        participant_exchange_participants = ExchangeParticipant.objects.filter(
            appuser=self.appuser,
            status='active'
        )
        invited_exchange_participants = ExchangeParticipant.objects.filter(
            appuser=self.appuser,
            status='invited'
        )
        created_exchanges = GiftExchange.objects.filter(created_by=self.appuser)
        invited_exchanges = [iep.giftexchange for iep in invited_exchange_participants]
        admin_exchanges = [aep.giftexchange for aep in admin_exchange_participants]
        participant_exchanges = [pep.giftexchange for pep in participant_exchange_participants]

        self.context.update({
            'admin_exchanges': admin_exchanges,
            'participant_exchanges': participant_exchange_participants,
            'invited_exchanges': invited_exchanges,
            'created_exchanges': created_exchanges
        })
        return HttpResponse(template.render(self.context, request))


class GiftExchangeHandleInvitation(GifteratorBase):
    def get(self, request, *args, **kwargs):
        if kwargs['action'] == 'accept':
            self.participant.status = 'active'
            messages.success(request, 'Invitation accepted!')
        else:
            self.participant.status = 'declined'
            messages.warning(request, 'Invitation declined.')
        self.participant.save()
        return redirect(reverse('gifterator_dashboard'))


class ExchangeParticipantDetail(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(ExchangeParticipantDetail, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('gifterator/giftexchange_participant_view.html')
        self.form = ParticipantDetailsForm
        self.context['breadcrumbs'] = [
            ('Gift Exchanges', reverse('gifterator_dashboard')),
            ('{} Details'.format(self.giftexchange.title), None)
        ]
        self.return_url = reverse('gifterator_exchange_participant_detail', kwargs={'ex_uuid': self.giftexchange.uuid})

    def get(self, request, *args, **kwargs):
        form = self.form(
            giftexchange=self.giftexchange,
            initial={
                '_likes': self.participant.likes,
                '_dislikes': self.participant.dislikes,
                '_allergies_or_sensitivities': self.participant.allergies_or_sensitivities,
                '_shipping_address': self.participant.shipping_address
            },

        )
        self.context['form'] = form
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(self.giftexchange, request.POST)
        if not self.giftexchange.locked:
            post_data = {field: str(value) for field, value in request.POST.items()}
            self.participant.update(**post_data)
            messages.success(request, 'Updated your details for "{}"'.format(self.giftexchange.title))
            return redirect(self.return_url)
        else:
            messages.error(request, 'This gift exchanged has been locked, you can no longer update your details')
            return redirect(self.return_url)


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
            user_exists = SessionManager.get_user_by_username_or_email(request.POST['email'])
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
            ]
        })
        self.exchange_details_form = GiftExchangeBaseForm
        self.participant_email_form = ParticipantEmailForm
        exchange_details_form = self.exchange_details_form(
            initial={
                'title': self.giftexchange.title,
                'description': self.giftexchange.description,
                'location': self.giftexchange.location,
                'date': self.giftexchange.date,
                'spending_limit': self.giftexchange.spending_limit,
                'exchange_in_person': self.giftexchange.exchange_in_person,
            }
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


class GiftExchangeAdminDashboardApi(GifteratorBase):
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
        self.exchange_details_form = GiftExchangeBaseForm
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

    def get(self, request, *args, **kwargs):
        return JsonResponse(self.data)

    def post(self, request, *args, **kwargs):
        post_target = request.POST.get('js_target')
        self.data.update({'postTarget': post_target})
        if post_target == 'email-search':
            search_results = SessionManager.search(request.POST['email'])
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
            user = SessionManager.get_user_by_username_or_email(request.POST['user-email'])
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
            participant = ExchangeParticipant.objects.get(user=user, giftexchange=self.giftexchange)
            if user == self.user:
                participant.status = 'inactive'
                participant.save()
            else:
                participant.delete()
            self.data.update(self._render_participant_list(request))
        elif post_target == 'update-details':
            exchange_details_form = self.exchange_details_form(request.POST)
            if exchange_details_form.is_valid():
                post_data = {field: str(value) for field, value in request.POST.items()}
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
                self.data.update({
                    'status': 'error',
                    'message': 'Form input invalid'
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
            self.data.update({
                'status': 'success',
                'html': False
            })

        self._refresh_data()
        return JsonResponse(self.data)

class GiftExchangeFormView(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(GiftExchangeFormView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/default.html')
        self.form = GiftExchangeCreateForm
        self.context['breadcrumbs'] = [
            ('Gift Exchanges', reverse('gifterator_dashboard')),
            ('Create Gift Exchange', None)
        ]

    def get(self, request, *args, **kwargs):
        form = self.form()

        self.context.update({'form': form})

        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            clean_post = {field: str(value) for field, value in request.POST.items()}
            giftexchange = GiftExchange.create(created_by=self.appuser, **clean_post)
            messages.success(request, 'Gift exchange "{}" created'.format(giftexchange.title))
            if request.POST.get('creater_is_participant') == 'on':
                status = 'active'
            else:
                status = 'inactive'
            participant = ExchangeParticipant.create(
                self.appuser,
                giftexchange,
                is_admin=True,
                status=status
            )
            if request.POST.get('creater_is_participant') == 'on':
                messages.success(request, 'You have been added as a participant of "{}"'.format(giftexchange.title))


            return redirect(
                reverse(
                    'gifterator_exchange_admin_dashboard',
                    kwargs={'ex_uuid': giftexchange.uuid}
                )
            )

        self.context.update({'form': form})

        return HttpResponse(self.template.render(self.context, request))
