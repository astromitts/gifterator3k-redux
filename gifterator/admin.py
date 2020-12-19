from django.contrib import admin
from gifterator.models import (
    GiftExchange,
    GiftExchangeParticipant
)

admin.site.register(GiftExchange)
admin.site.register(GiftExchangeParticipant)
