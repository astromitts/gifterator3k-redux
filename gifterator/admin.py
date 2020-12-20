from django.contrib import admin
from gifterator.models import (
    GiftExchange,
    ExchangeParticipant
)

admin.site.register(GiftExchange)
admin.site.register(ExchangeParticipant)
