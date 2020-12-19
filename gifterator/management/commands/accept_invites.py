from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from gifterator.models import AppUser, GiftExchange

import random


TEST_USERS = [
    ('olliever@example.com', 'Oliver', 'Henry'),
    ('tross@example.com', 'Thomas', 'Ross'),
    ('myfang@example.com', 'Matthew', 'Fang'),
    ('edtalbot@example.com', 'Edward', 'Talbot'),
    ('batty@example.com', 'Hank', 'Bates'),
    ('vonb@example.com', 'Ben', 'Von'),
    ('liver@example.com', 'Olivia', 'Richmond'),
    ('lizbet@example.com', 'Elizabeth', 'Jones'),
    ('eyeriss@example.com', 'Iris', 'French'),
    ('emily.rivera@example.com', 'Emily', 'Rivera'),
    ('ameliaaa@example.com', 'Amelia', 'Lee'),
    ('graceg@example.com', 'Grace', 'Gregg'),
]

FAKE_LIKES = [
    None,
    'cats, crafts, magazines',
    'dogs, beer, tabletop games',
    'reading, podcasts, watching sports',
    'food, snacks, candy',
    'socks, novelty hats, golfing',
    'fizzy water, especially Topo Chico'
]

FAKE_DISLIKES = [
    None,
    'socks and mugs',
    'calendars',
    'coffee, tea, caffienated beverages in general',
    'not much!',
    'Scary movies, the news, pop music'
]

FAKE_ALLERGIES = [
    None,
    'Hay, pollen',
    'Tree nuts',
    'Dairy',
    'Penicillin'
]

FAKE_ADDRESSES = [
    '759  Shearwood Forest Drive, Manchester NH',
    '3679  Alexander Drive, Wichita Falls KS',
    '121  Daffodil Lane, McLean VA',
    '4690  Norma Avenue, Jefferson WI',
    '2135  Reynolds Alley, Freemont CA',
    '3881  Fort Street, Washington NC',
    '3466  Carolina Avenue, Durango CO',
    '2464  Mulberry Avenue, El Paso TX',
    '2461  Oakridge Lane, Dallas TX',
]


class Command(BaseCommand):
    help = 'Pre-populates test user instances'

    def add_arguments(self, parser):
        parser.add_argument('ex_uuid', type=str)

    def handle(self, *args, **options):
        uuid = options['ex_uuid']
        exchange = GiftExchange.objects.get(uuid=uuid)
        invitees = exchange.giftexchangeparticipant_set.filter(
            appuser__user__email__icontains='@example.com').all()
        for invitee in invitees:
            invitee.status = 'active'
            invitee.likes = random.choice(FAKE_LIKES)
            invitee.dislikes = random.choice(FAKE_DISLIKES)
            invitee.allergies_or_sensitivities = random.choice(FAKE_ALLERGIES)
            invitee.shipping_address = random.choice(FAKE_ADDRESSES)
            invitee.save()
