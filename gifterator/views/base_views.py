from django.views import View
from django.http import JsonResponse
from gifterator.models import (
    GiftExchange,
    ExchangeParticipant,
    AppUser,
)


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

            if self.giftexchange.participants_notified:
                self.assignment = self.participant.giver_assignment
            else:
                self.assignment = None

            self.context.update({
                'user': self.user,
                'appuser': self.appuser,
                'giftexchange': self.giftexchange,
                'participant': self.participant,
                'assignment': self.assignment,
                'participant_list': self.participant_list,
                'invited_list': self.invited_list,
                'assignment_list': self.assigment_list
            })
