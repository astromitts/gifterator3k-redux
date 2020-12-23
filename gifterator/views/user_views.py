from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, resolve_url
from django.template import loader
from django.urls import reverse
from django.utils.safestring import mark_safe

from datetime import datetime

from gifterator.forms import (
    CreateGiftspoForm,
    GiftspoItemForm,
    GiftExchangeBaseForm,
    GiftExchangeCreateForm,
    ParticipantDetailsForm,
    UserDefaultForm,
)
from gifterator.mailer import GifteratorMailer
from gifterator.models import (
    ExchangeAssignment,
    GiftExchange,
    GiftList,
    GiftListItem,
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
        form = self.form(initial={'created_by_pk': self.appuser.pk})

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


class GiftspoListDashboard(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(GiftspoListDashboard, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('gifterator/giftspo_list_dashboard.html')
        self.giftspo_lists = self.appuser.giftlist_set.all()
        self.context.update({
            'giftspo_lists': self.giftspo_lists,
            'breadcrumbs': [
                ('Profile', reverse('session_manager_profile')),
                ('Giftspo Lists', None)
            ]
        })

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.template.render(self.context, request))


class CreateGiftspoView(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(CreateGiftspoView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('session_manager/default.html')
        self.form = CreateGiftspoForm
        if kwargs.get('list_uuid'):
            self.giftspo_list = GiftList.objects.get(uuid=kwargs['list_uuid'])
            self.context.update({
                'breadcrumbs': [
                    ('Profile', reverse('session_manager_profile')),
                    ('Giftspo Lists', reverse('gifterator_user_giftspo_dashboard')),
                    ('Edit: {}'.format(self.giftspo_list.nickname), None)
                ]
            })
        else:
            self.giftspo_list = None
            self.context.update({
                'breadcrumbs': [
                    ('Profile', reverse('session_manager_profile')),
                    ('Giftspo Lists', reverse('gifterator_user_giftspo_dashboard')),
                    ('New', None)
                ]
            })

    def get(self, request, *args, **kwargs):
        if self.giftspo_list:
            self.context.update({
                'form': self.form(
                    initial={
                        'nickname': self.giftspo_list.nickname
                    }
                )
            })
        else:
            self.context.update({
                'form': self.form()
            })
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():

            if self.giftspo_list:
                self.giftspo_list.nickname = request.POST['nickname']
                self.giftspo_list.save()
                return redirect(reverse('gifterator_user_giftspo_dashboard'))

            new_giftspo = GiftList(appuser=self.appuser, nickname=request.POST['nickname'])
            new_giftspo.save()
            messages.success(request, 'Created your Giftspo List! Now add stuff to it!')
            return_url = reverse(
                'gifterator_user_giftspo_additem',
                kwargs={
                    'list_uuid': new_giftspo.uuid
                }
            )
            return redirect(return_url)
        else:
            messages.error(request, 'Something went wrong!')
            self.context.update({
                'form': form
            })
            return HttpResponse(self.template.render(self.context, request))


class DeleteGiftspoView(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(DeleteGiftspoView, self).setup(request, *args, **kwargs)
        self.giftspo_list = GiftList.objects.get(uuid=kwargs['list_uuid'])
        self.return_url = reverse('gifterator_user_giftspo_dashboard')
        self.context.update({
            'breadcrumbs': [
                ('Profile', reverse('session_manager_profile')),
                ('Giftspo Lists', reverse('gifterator_user_giftspo_dashboard')),
                ('Delete', None)
            ]
        })

    def get(self, request, *args, **kwargs):
        template = loader.get_template('gifterator/confirm_action.html')
        self.context.update({
            'confirm_text': 'Permantently delete Giftspo list "{}"'.format(self.giftspo_list.nickname),
            'cancel_action': self.return_url
        })
        return HttpResponse(template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        messages.info(request, 'Deleted Giftspo List "{}"'.format(self.giftspo_list.nickname))
        self.giftspo_list.delete()
        return redirect(self.return_url)


class GiftspoItemView(GifteratorBase):
    def setup(self, request, *args, **kwargs):
        super(GiftspoItemView, self).setup(request, *args, **kwargs)
        self.template = loader.get_template('gifterator/giftspo_list_item.html')
        self.giftspo_list = GiftList.objects.get(uuid=kwargs['list_uuid'])
        self.context.update({
            'breadcrumbs': [
                ('Profile', reverse('session_manager_profile')),
                ('Giftspo Lists', reverse('gifterator_user_giftspo_dashboard')),
                ('Add/Edit Item', None)
            ],
        })
        if kwargs.get('item_uuid'):
            self.giftlistitem = GiftListItem.objects.get(uuid=kwargs['item_uuid'])
            self.reload_url = None
        else:
            self.giftlistitem = None
            self.reload_url = reverse(
                'gifterator_user_giftspo_additem',
                kwargs={
                    'list_uuid': self.giftspo_list.uuid
                }
            )
        self.form = GiftspoItemForm
        self.back_url = reverse('gifterator_user_giftspo_dashboard')

    def get(self, request, *args, **kwargs):
        if self.giftlistitem:
            self.context.update({
                'form': self.form(initial={
                    'web_link': self.giftlistitem.web_link,
                    'description': self.giftlistitem.description,
                    'nickname': self.giftlistitem.nickname
                })
            })
        else:
            self.context.update({
                'form': self.form()
            })
        return HttpResponse(self.template.render(self.context, request))

    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            if self.giftlistitem:
                self.giftlistitem.nickname = request.POST['nickname']
                self.giftlistitem.web_link = request.POST['web_link']
                self.giftlistitem.description = request.POST['description']
                self.giftlistitem.save()
                messages.success(request, 'Updated item.')
                return redirect(self.back_url)
            else:
                giftlistitem = GiftListItem(
                    giftlist=self.giftspo_list,
                    nickname=request.POST['nickname'],
                    web_link=request.POST['web_link'],
                    description=request.POST['description'],
                )
                giftlistitem.save()
                messages.success(
                    request,
                    mark_safe(
                        'List updated! Add another item or&nbsp;<a href="{}">go back to your Giftspo lists</a>.'.format(
                            self.back_url
                        )
                    )
                )
                return redirect(self.reload_url)
        else:
            messages.error(request, 'Something went wrong!')
            self.context.update({
                'form': form
            })
            return HttpResponse(self.template.render(self.context, request))


class CreateGiftspoDeleteItem(GifteratorBase):
    def post(self, request, *args, **kwargs):
        return_url = reverse('gifterator_user_giftspo_dashboard')
        item = GiftListItem.objects.get(uuid=kwargs['item_uuid'])
        item.delete()
        return redirect(return_url)
