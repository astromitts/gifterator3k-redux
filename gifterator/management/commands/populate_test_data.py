from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from gifterator.models import AppUser

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


    def handle(self, *args, **options):
        for test_data in TEST_USERS:
            email = test_data[0]
            first_name = test_data[1]
            last_name = test_data[2]
            # User.objects.filter(email=email).all().delete()
            new_user = User.objects.filter(email=email).first()
            if not new_user:
                new_user = User(
                    email=email,
                    username=email,
                    first_name=first_name,
                    last_name=last_name
                )
                new_user.save()
            new_user.set_password('password')
            new_user.save()
            appuser = AppUser.objects.filter(user=new_user).first()
            appuser.likes = random.choice(FAKE_LIKES)
            appuser.dislikes = random.choice(FAKE_DISLIKES)
            appuser.allergies_or_sensitivities = random.choice(FAKE_ALLERGIES)
            appuser.shipping_address = random.choice(FAKE_ADDRESSES)
            appuser.save()
