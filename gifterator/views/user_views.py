from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, resolve_url
from django.template import loader
from django.urls import reverse

from datetime import datetime

from gifterator.forms import (
    GiftExchangeBaseForm,
    GiftExchangeCreateForm,
    ParticipantDetailsForm,
    UserDefaultForm,
)
from gifterator.mailer import GifteratorMailer
from gifterator.models import (
    ExchangeAssignment,
    GiftExchange,
    ExchangeParticipant,
    AppUser,
)

from gifterator.views.base_views import GifteratorBase


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
            status='active',
            giftexchange__date__gte=datetime.today()
        )
        invited_exchange_participants = ExchangeParticipant.objects.filter(
            appuser=self.appuser,
            status='invited',
            giftexchange__locked=False,
            giftexchange__date__gte=datetime.today()
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


class ExchangeDetail(GifteratorBase):
    def get(self, request, *args, **kwargs):
        self.template = loader.get_template('gifterator/exchange_detail.html')
        return HttpResponse(self.template.render(self.context, request))


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
