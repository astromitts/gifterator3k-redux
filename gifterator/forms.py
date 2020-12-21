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
)

from gifterator.models import (
    GiftExchange,
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
    exchange_in_person=BooleanField(
        widget=CheckboxInput(attrs={'class': 'form-control'}),
        label='This gift exchange will take in place in person (e.g. not on a virtual hangout or asynchronously)',
        help_text='If the exchange is not in person, participants will be required to provide a shipping address',
        required=False
    )


class GiftExchangeCreateForm(GiftExchangeBaseForm, ModelForm):
    creater_is_participant = BooleanField(
        label='I am a participant in this giftexchange',
        help_text='This will automatically include you in the gift exchange participant list',
        widget=CheckboxInput(attrs={'class': 'form-control', 'checked': 'checked'}),
        required=False
    )
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
