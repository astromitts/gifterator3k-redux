from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Make me a superuser shortcut'

    def handle(self, *args, **options):
        me = User.objects.get(email='morinbe@gmail.com')
        me.is_staff = True
        me.is_superuser = True
        me.save()
