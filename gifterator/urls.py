from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from gifterator.views.user_views import *
from gifterator.views.exchange_admin_views import *

urlpatterns = [
    path('', GiftExchangeDashboard.as_view(), name='gifterator_dashboard'),
    path('profile/default-settings/', UserDefaultManager.as_view(), name='gifterator_user_manager_defaults'),
    path('profile/giftspo-lists/', GiftspoListDashboard.as_view(), name='gifterator_user_giftspo_dashboard'),
    path('profile/giftspo-lists/create/', CreateGiftspoView.as_view(), name='gifterator_user_giftspo_create'),
    path('profile/giftspo-lists/<str:list_uuid>/edit/', CreateGiftspoView.as_view(), name='gifterator_user_giftspo_edit'),
    path('profile/giftspo-lists/<str:list_uuid>/add-item/', GiftspoItemView.as_view(), name='gifterator_user_giftspo_additem'),
    path('profile/giftspo-lists/<str:list_uuid>/delete/', DeleteGiftspoView.as_view(), name='gifterator_user_giftspo_delete'),
    path('profile/giftspo-lists/<str:list_uuid>/item/<str:item_uuid>/edit/', GiftspoItemView.as_view(), name='gifterator_user_giftspo_edititem'),
    path('profile/giftspo-lists/<str:list_uuid>/item/<str:item_uuid>/delete/', CreateGiftspoDeleteItem.as_view(), name='gifterator_user_giftspo_deleteitem'),
    path('giftexchanges/create/', GiftExchangeFormView.as_view(), name='gifterator_create_giftexchange'),
    path('giftexchanges/<str:ex_uuid>/', ExchangeDetail.as_view(), name='gifterator_exchange_detail'),
    path('giftexchanges/<str:ex_uuid>/mydetails/', ExchangeParticipantDetail.as_view(), name='gifterator_exchange_participant_detail'),
    path('giftexchanges/<str:ex_uuid>/invitation/<str:action>/', GiftExchangeHandleInvitation.as_view(), name='gifterator_exchange_handle_invitation'),
    path('giftexchanges/<str:ex_uuid>/admin/', GiftExchangeAdminDashboard.as_view(), name='gifterator_exchange_admin_dashboard'),
    path('giftexchanges/<str:ex_uuid>/admin/inviteappuser/', GiftExchangeAdminAppInvite.as_view(), name='gifterator_exchange_admin_invite_user'),
    path('giftexchanges/<str:ex_uuid>/admin/sendemail/<str:mail_type>/', GiftExchangeAdminEmailer.as_view(), name='gifterator_exchange_admin_sendmail'),
    path('giftexchanges/<str:ex_uuid>/api/', GiftExchangeAdminDashboardApi.as_view(), name='gifterator_exchange_admin_dashboard_api'),
]
