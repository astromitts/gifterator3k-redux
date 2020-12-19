from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from session_manager.views import *

urlpatterns = [
    path('end-user-license/', TemplateView.as_view(template_name='session_manager/includes/eula.html'), name='eula'),
    path('privacy-policy/', TemplateView.as_view(template_name='session_manager/includes/privacy_policy.html'), name='privacy_policy'),
    path('admin/', admin.site.urls),
    path('register/', CreateUserView.as_view(), name='session_manager_register'),
    path('login/', LoginUserView.as_view(), name='session_manager_login'),
    path('logout/', LogOutUserView.as_view(), name='session_manager_logout'),
    path('sendresetpassword/', SendPasswordResetLink.as_view(), name='session_manager_send_reset_password_link'),
    path('sendregistrationlink/', SendRegistrationLink.as_view(), name='session_manager_send_registration_link'),
    path('resetpassword/', ResetPasswordWithTokenView.as_view(), name='session_manager_token_reset_password'),
    path('profile/resetpassword/', ResetPasswordFromProfileView.as_view(), name='session_manager_profile_reset_password'),
    path('profile/update/', UpdateProfileView.as_view(), name='session_manager_profile_update'),
    path('profile/', Profile.as_view(), name='session_manager_profile'),
]

from gifterator.urls import urlpatterns as app_urls

urlpatterns = urlpatterns + app_urls
