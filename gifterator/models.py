from django.db import models
from django.contrib.auth.models import User
from session_manager.models import AppUser
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime
import uuid


class BaseModel(models.Model):
    class Meta:
        abstract = True

    def update(self, **kwargs):
        for field, value in kwargs.items():
            if hasattr(self, field):
                if value == 'on':
                    value = True
                setattr(self, field, value)
        self.save()


class UserDefault(BaseModel):
    appuser = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    likes = models.TextField(blank=True, null=True)
    dislikes = models.TextField(blank=True, null=True)
    allergies_or_sensitivities = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)

@receiver(post_save, sender=AppUser)
def create_user_default_instance(sender, instance, **kwargs):
    userdefault = UserDefault.objects.filter(appuser=instance).first()
    if not userdefault:
        userdefault = UserDefault(appuser=instance)
        userdefault.save()

class GiftExchange(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4)
    title = models.CharField(max_length=250, unique=True)
    created_by = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField(null=True, blank=True)
    location = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    spending_limit = models.IntegerField(null=True, blank=True)
    exchange_in_person = models.BooleanField(default=True)
    locked = models.BooleanField(default=False)
    participants_notified = models.BooleanField(default=False)

    def __str__(self):
        return '<GiftExchange: {}, title: {}>'.format(self.uuid, self.title)

    @classmethod
    def boolean_fields(cls):
        """ helper for form processing """
        return ['exchange_in_person', 'locked', 'participants_notified']

    @classmethod
    def create(cls, created_by, **kwargs):
        new_instance = cls()
        new_instance.created_by = created_by
        new_instance.title = kwargs['title']
        new_instance.date = kwargs['date']
        new_instance.location = kwargs['location']
        new_instance.description = kwargs['description']
        new_instance.spending_limit = kwargs['spending_limit']
        new_instance.exchange_in_person = kwargs.get('exchange_in_person') == 'on'
        new_instance.save()
        return new_instance

    def _generate_assignments(self):
        starting_giver = self.exchangeparticipant_set.filter(status='active').order_by('?').first()
        current_giver = starting_giver

        participants = self.exchangeparticipant_set.filter(status='active').all()
        assignments = []
        reciever_appusers = [starting_giver, ]
        while len(assignments) <= self.exchangeparticipant_set.filter(status='active').all().count() - 2:
            exclusions = reciever_appusers + [current_giver]
            random_reciever_qs = self.exchangeparticipant_set.filter(status='active').exclude(pk__in=[ex.pk for ex in exclusions])
            random_reciever = random_reciever_qs.order_by('?').first()

            if random_reciever:
                assignments.append((current_giver, random_reciever))
                reciever_appusers.append(random_reciever)
                current_giver = random_reciever

        final_giver = current_giver
        assignments.append((final_giver, starting_giver))
        return assignments

    def _verify_closed_loop(self, assignments):
        def _get_reciever_for_participant(qgiver, assignments):
            for giver, reciever in assignments:
                if giver == qgiver:
                    return reciever

        # print('Checking loop is closed....')
        loop_is_closed = False
        expected_connection_count = len(assignments)
        checked_recievers = []
        first_giver = assignments[0][0]
        first_reciever = assignments[0][1]

        giver = first_giver
        reciever = first_reciever
        while first_giver not in checked_recievers:
            # print('{} gives to {}'.format(giver, reciever))
            checked_recievers.append(reciever)
            giver = reciever
            reciever = _get_reciever_for_participant(giver, assignments)

        loop_is_closed = len(checked_recievers) == expected_connection_count
        return loop_is_closed

    def generate_assignemnts(self, override_lock=False):
        if self.locked and not override_lock:
            raise Exception('Assignments are locked for this gift exchange')
        # print('Removing old assignments...')
        self.exchangeassignment_set.all().delete()
        # print('Making assignments...')
        loop_is_closed = False
        tries = 0
        while not loop_is_closed:
            assignments = self._generate_assignments()
            loop_is_closed = self._verify_closed_loop(assignments)
            tries += 1

        # print("Took {} tries".format(tries))
        assignment_objects = []
        for giver_participant, reciever_participant in assignments:
            new_assignment = ExchangeAssignment(
                giftexchange=self,
                giver=giver_participant,
                reciever=reciever_participant
            )
            new_assignment.save()
            assignment_objects.append(new_assignment)
        return assignment_objects


class ExchangeParticipant(BaseModel):
    giftexchange = models.ForeignKey(GiftExchange, on_delete=models.CASCADE)
    appuser = models.ForeignKey(AppUser, on_delete=models.CASCADE)
    _likes = models.TextField(blank=True, null=True)
    _dislikes = models.TextField(blank=True, null=True)
    _allergies_or_sensitivities = models.TextField(blank=True, null=True)
    _shipping_address = models.TextField(blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=(
            ('pending', 'pending'),
            ('active', 'active'),
            ('inactive', 'inactive'),
            ('invited', 'invited'),
            ('declined', 'declined')
        ),
        default='active'
    )
    email_sent = models.BooleanField(default=False)
    email_last_sent = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.appuser.user:
            return '<Participant: {} ({})> // {}'.format(
                self.appuser.user.email,
                self.status,
                self.giftexchange
            )
        else:
            token = self.appuser.usertoken_set.first()
            if token:
                token_str = token.token
            else:
                token_str = 'unknown'
            return '<Participant: (pending) token: {}> // {}'.format(
                token_str,
                self.giftexchange,
            )

    @property
    def likes(self):
        if self._likes:
            return self._likes
        return self.appuser.userdefault.likes

    @property
    def dislikes(self):
        if self._dislikes:
            return self._dislikes
        return self.appuser.userdefault.dislikes

    @property
    def allergies_or_sensitivities(self):
        if self._allergies_or_sensitivities:
            return self._allergies_or_sensitivities
        return self.appuser.userdefault.allergies_or_sensitivities

    @property
    def shipping_address(self):
        if self._shipping_address:
            return self._shipping_address
        return self.appuser.userdefault.shipping_address

    @classmethod
    def create(cls, appuser, giftexchange, is_admin=False, status='active'):
        new_instance = cls(
            appuser=appuser,
            giftexchange=giftexchange,
            is_admin=is_admin
        )
        new_instance.save()
        return new_instance

    @classmethod
    def get_or_create(cls, appuser, giftexchange, status='invited'):
        instance = cls.objects.filter(appuser=appuser, giftexchange=giftexchange).first()
        if not instance:
            instance = cls(
                appuser=appuser,
                giftexchange=giftexchange
            )
        instance.status = status
        instance.is_admin = False
        instance.save()
        return instance

    @property
    def giver_assignment(self):
        return ExchangeAssignment.objects.filter(
            giftexchange=self.giftexchange,
            giver=self
        ).first()

    @property
    def reciever_assignment(self):
        return ExchangeAssignment.objects.filter(
            giftexchange=self.giftexchange,
            reciever=self
        ).first()

    @property
    def first_name(self):
        return self.appuser.user.first_name

    @property
    def last_name(self):
        return self.appuser.user.last_name

    @property
    def full_name(self):
        return self.appuser.user.get_full_name()

    @property
    def email(self):
        return self.appuser.user.email


class ExchangeAssignment(BaseModel):
    giftexchange = models.ForeignKey(GiftExchange, on_delete=models.CASCADE)
    giver = models.ForeignKey(ExchangeParticipant, on_delete=models.CASCADE, related_name='giftexchange_giver')
    reciever = models.ForeignKey(ExchangeParticipant, on_delete=models.CASCADE, related_name='giftexchange_reciever')

