from django.urls import path
from gifterator.views import *

urlpatterns = [
    path('', GiftExchangeDashboard.as_view(), name='gifterator_dashboard'),
    path('giftexchanges/create/', GiftExchangeFormView.as_view(), name='gifterator_create_giftexchange'),
    path('giftexchanges/<str:ex_uuid>/', GiftExchangeParticipantdetail.as_view(), name='gifterator_exchange_participant_detail'),
    path('giftexchanges/<str:ex_uuid>/invitation/<str:action>/', GiftExchangeHandleInvitation.as_view(), name='gifterator_exchange_handle_invitation'),
    path('giftexchanges/<str:ex_uuid>/admin/', GiftExchangeAdminDashboard.as_view(), name='gifterator_exchange_admin_dashboard'),
    path('giftexchanges/<str:ex_uuid>/admin/inviteappuser/', GiftExchangeAdminAppInvite.as_view(), name='gifterator_exchange_admin_invite_user'),
    path('giftexchanges/<str:ex_uuid>/admin/sendemail/<str:mail_type>/', GiftExchangeAdminEmailer.as_view(), name='gifterator_exchange_admin_sendmail'),
    path('giftexchanges/<str:ex_uuid>/api/', GiftExchangeAdminDashboardApi.as_view(), name='gifterator_exchange_admin_dashboard_api'),
]
