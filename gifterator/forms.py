from django.core.exceptions import ValidationError
from django.forms import (
    BooleanField,
    CheckboxInput,
    CharField,
    ChoiceField,
    DateInput,
    EmailField,
    EmailInput,
    Form,
    HiddenInput,
    ModelForm,
    NumberInput,
    Textarea,
    TextInput,
    Select,
    URLInput,
)

from gifterator.models import (
    AppUser,
    GiftExchange,
    GiftList,
    GiftListItem,
    ExchangeParticipant,
    UserDefault,
)


class UserDefaultForm(ModelForm):
    class Meta:
        model = UserDefault
        fields = [
            'likes',
            'dislikes',
            'allergies_or_sensitivities',
            'shipping_address',
        ]
        widgets = {}
        for field in fields:
            widgets[field] = Textarea(attrs={'class': 'form-control', 'rows': 5})


class ParticipantExchangeGiftList(ModelForm):
    pass


class ParticipantDetailsForm(ModelForm):

    def __init__(self, giftexchange, *args, **kwargs):
        super(ParticipantDetailsForm, self).__init__(*args, **kwargs)
        if giftexchange.locked:
            field_attrs={'class': 'form-control', 'rows': 5, 'disabled': 'disabled'}
        else:
            field_attrs={'class': 'form-control', 'rows': 5}
        if not giftexchange.exchange_in_person:
            self.fields['_shipping_address'].help_text = (
                'This gift exchange is not taking place in person, so providing a shipping is '
                'required. The shipping address you provide will be shared only with your gift '
                'giver.'
            )
        else:
            self.fields['_shipping_address'].help_text = (
                'This gift exchange is taking place in person, so providing a shipping address '
                'is optional. If you choose to provide it, it will '
                'be shared with your gift giver.'
            )

        for field_name in self.fields:
            if not giftexchange.exchange_in_person and field_name == '_shipping_address':
                self.fields[field_name].widget = HiddenInput()
            else:
                self.fields[field_name].widget = Textarea(attrs=field_attrs)

    class Meta:
        model = ExchangeParticipant
        fields = [
            '_likes',
            '_dislikes',
            '_allergies_or_sensitivities',
            '_shipping_address',
        ]


class GiftExchangeBaseForm(Form):
    js_target = CharField(
        widget=HiddenInput(attrs={'value': 'update-details'})
    )
    title = CharField(
        widget=TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    date = CharField(
        widget=DateInput(attrs={'class':'datepicker form-control', 'autocomplete': 'off'})
    )
    location = CharField(
        widget=TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    description = CharField(
        widget=Textarea(attrs={
            'class': 'form-control',
            'autocomplete': 'off',
            'rows': 5
        }),
        required=False
    )
    spending_limit = CharField(
        widget=NumberInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    exchange_in_person = BooleanField(
        widget=CheckboxInput(attrs={'class': 'form-control'}),
        label='This gift exchange will take in place in person (e.g. not on a virtual hangout or asynchronously)',
        help_text='If the exchange is not in person, participants will be required to provide a shipping address',
        required=False
    )
    created_by_pk = CharField(
        widget=HiddenInput()
    )
    giftexchange_pk = CharField(
        widget=HiddenInput()
    )

    def __init__(self, giftexchange, non_model_initial, *args, **kwargs):
        super(GiftExchangeBaseForm, self).__init__(*args, **kwargs)
        self.giftexchange = giftexchange
        self.created_by = AppUser.objects.get(pk=non_model_initial['created_by_pk'])
        if not self.has_changed():
            for field in self.fields:
                if hasattr(giftexchange, field):
                    init_value = getattr(giftexchange, field)
                    if init_value is True:
                        self.fields[field].widget.attrs.update({
                            'checked': 'checked'
                        })
                    elif init_value is False:
                        pass
                    else:
                        self.fields[field].widget.attrs.update({
                            'value': init_value
                        })
                elif field in non_model_initial:
                    self.fields[field].widget.attrs.update({
                        'value': non_model_initial[field]
                    })

    def clean_title(self):
        """ Enforces username and password requirements
        """
        super(GiftExchangeBaseForm, self).clean()
        data = self.cleaned_data
        appuser_other_exchanges = GiftExchange.objects.exclude(
            pk=self.giftexchange.pk).filter(
            created_by=self.created_by
        ).all()
        exchange_titles = [ge.title.lower() for ge in appuser_other_exchanges]
        if data['title'].lower() in exchange_titles:
            raise ValidationError('You already have a gift exchange with that title.')
        return data['title']


class GiftExchangeCreateForm(GiftExchangeBaseForm, ModelForm):
    creater_is_participant = BooleanField(
        label='I am a participant in this giftexchange',
        help_text='This will automatically include you in the gift exchange participant list',
        widget=CheckboxInput(attrs={'class': 'form-control', 'checked': 'checked'}),
        required=False
    )
    created_by_pk = CharField(widget=HiddenInput())

    class Meta:
        model = GiftExchange
        fields = [
            'title',
            'date',
            'location',
            'description',
            'spending_limit',
            'exchange_in_person',
        ]
        widgets = {
            'created_by_pk': HiddenInput()
        }

    def clean(self):
        """ Enforces username and password requirements
        """
        super(GiftExchangeCreateForm, self).clean()
        data = self.cleaned_data
        appuser = AppUser.objects.get(pk=data['created_by_pk'])
        appuser_exchanges = GiftExchange.objects.filter(created_by=appuser).all()
        exchange_titles = [ge.title.lower() for ge in appuser_exchanges]
        if data['title'].lower() in exchange_titles:
            raise ValidationError('You already have a gift exchange with that title.')
        return data


class ParticipantEmailForm(Form):
    js_target = CharField(
        widget=HiddenInput(attrs={'value': 'email-search'})
    )
    email = CharField(widget=EmailInput(attrs={'class': 'form-control'}))


class InvitationEmailForm(Form):
    email = EmailField(widget=EmailInput(attrs={'class': 'form-control'}))


class SendMessageForm(Form):
    js_target = CharField(
        widget=HiddenInput(attrs={'value': 'send-bulk-message'})
    )
    target = ChoiceField(
        widget=Select(
            attrs={
                'class': 'form-control',
                'id': 'id_bulk_message_target'
            }
        ),
        choices=[
            ('all', 'all'),
            ('invited', 'invited'),
            ('active', 'active')
        ]
    )
    message = CharField(
        widget=Textarea(
            attrs={
                'class': 'form-control',
                'id': 'id_bulk_message_body'
            }
        ),
        help_text='Plain text only! Any HTML or script tags will be stripped from your message.'
    )


class CreateGiftspoForm(ModelForm):
    class Meta:
        model = GiftList
        fields = ['nickname']
        widgets = {
            'nickname': TextInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'nickname': 'Give your list a memorable name'
        }

        help_texts = {
            'nickname': 'Plain text only! Any HTML or script tags will be stripped from your message. This will only be visible to you'
        }

class GiftspoItemForm(ModelForm):
    submit_done_url = CharField(widget=HiddenInput())
    class Meta:
        model = GiftListItem
        fields = ['web_link', 'name', 'description', 'meta']
        widgets = {
            'web_link': URLInput(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'description': Textarea(attrs={
                'class': 'form-control',
                'autocomplete': 'off',
                'rows': 5
            }),
            'meta': HiddenInput()
        }
        help_texts = {
            'name': 'Plain text only! Any HTML or script tags will be stripped from your message.',
            'description': 'Plain text only! Any HTML or script tags will be stripped from your message.'
        }
