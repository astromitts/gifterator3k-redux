from django.contrib import admin
from gifterator.models import (
    GiftExchange,
    GiftList,
    GiftListItem,
    ExchangeParticipant,
)

admin.site.register(GiftExchange)
admin.site.register(GiftList)
admin.site.register(GiftListItem)
admin.site.register(ExchangeParticipant)
