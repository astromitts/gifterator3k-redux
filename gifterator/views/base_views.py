from django.views import View
from django.http import JsonResponse
from gifterator.models import (
    GiftExchange,
    ExchangeParticipant,
    AppUser,
)
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import requests


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


class MetaDataFetcher(View):
    def setup(self, request, *args, **kwargs):
        super(MetaDataFetcher, self).setup(request, *args, **kwargs)
        self.target_url = request.POST['targetUrl']

    def _get_mostsite_data(self, content):
        description = content.head.find('meta', {'property': 'og:description'})
        if description:
            description = description['content']
        else:
            description = None

        title = content.head.find('meta', {'property': 'og:title'})
        if title:
            title = title['content']
        else:
            title = content.title.text

        canonical = content.head.find('link', {'rel': 'canonical'})
        if canonical:
            canonical = canonical['href']
        else:
            canonical = self.target_url
        pagedata = {
            'title': title,
            'description': description,
            'url': canonical,
        }
        return pagedata

    def post(self, request, *args, **kwargs):
        pagedata = {
            'title': None,
            'description': None,
            'url': self.target_url,
        }
        try:
            req = requests.get(
                self.target_url,
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"
                }
            )

            content = BeautifulSoup(req.content)
            parsed_url = urlparse(self.target_url)
            # amazon is the woooorrrrst and blocks automated HTTP calls
            if req.status_code == 200:
                if parsed_url.hostname == 'www.amazon.com':
                    pagedata = pagedata = {
                        'title': None,
                        'description': None,
                        'url': self.target_url.replace('?{}'.format(parsed_url.query), ''),
                        'image': None,
                    }
                else:
                    pagedata = self._get_mostsite_data(content)
        except Exception:
            pass
        return JsonResponse(pagedata)

