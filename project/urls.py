from django.contrib import admin
from django.urls import path

from session_manager.views import *

urlpatterns = [
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
    path('', Profile.as_view(), name='session_manager_profile'),
]
