from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from session_manager.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('end-user-license/', TemplateView.as_view(template_name='session_manager/includes/eula.html'), name='eula'),
    path('privacy-policy/', TemplateView.as_view(template_name='session_manager/includes/privacy_policy.html'), name='privacy_policy'),
]

from session_manager.urls import urlpatterns as session_urls
urlpatterns = urlpatterns + session_urls

from gifterator.urls import urlpatterns as app_urls
urlpatterns = urlpatterns + app_urls
