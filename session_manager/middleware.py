from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404

from gifterator.models import GiftExchange, GiftExchangeParticipant


def session_request_validation(get_response):
    """ Handler for catching unauthenticated requests to authentication
        protected views and returning an error page instead of DEBUG page

        Primarily exists because Heroku has a real hard time with DEBUG=False
    """

    def middleware(request):
        error_message = None
        status_code = 200

        # middleware does not have access to the user
        # session_manager_login is expected to set a session variable to use here
        user_is_authenticated = request.session.get('user_is_authenticated')

        try:
            resolved_url = resolve(request.path)
            is_login_page = resolved_url.url_name == settings.AUTHENTICATION_REQUIRED_REDIRECT
            if is_login_page and user_is_authenticated:
                return redirect(reverse(settings.LOGIN_SUCCESS_REDIRECT))
            if not resolved_url.url_name in settings.AUTHENTICATION_EXEMPT_VIEWS:
                if not user_is_authenticated:
                    request.session['login_redirect_from'] = request.path
                    messages.error(
                        request,
                        'You must be authenticated to access this page. Please log in.'
                    )
                    return redirect(reverse(settings.AUTHENTICATION_REQUIRED_REDIRECT))
                else:
                    request.session['login_redirect_from'] = None

            if 'ex_uuid' in resolved_url.kwargs:
                giftexchange = GiftExchange.objects.filter(uuid=resolved_url.kwargs['ex_uuid']).first()
                if not giftexchange:
                    error_message = 'Gift exchange not found.'
                    status_code = 404
                else:
                    user = User.objects.get(pk=request.session['_auth_user_id'])
                    participant = GiftExchangeParticipant.objects.filter(
                        appuser=user.appuser,
                        giftexchange=giftexchange,
                        status__in=['active', 'invited']).first()
                    if not participant:
                        error_code = 503
                        error_message = 'Permission denied: you are not a participant of this gift exchange'
                    elif '/admin/' in request.path and not participant.is_admin:
                        error_code = 503
                        error_message = 'Permission denied: you are not admin of this gift exchange.'

        except Resolver404:
            if not settings.MIDDLEWARE_DEBUG:
                error_message = 'Page not found.'
                status_code = 404

        if error_message:
            if not settings.MIDDLEWARE_DEBUG:
                context = {
                    'error_message': error_message,
                    'status_code': status_code
                }
                return render(
                    request,
                    settings.DEFAULT_ERROR_TEMPLATE,
                    context=context,
                    status=status_code
                )
            else:
                raise Exception(error_message)
        else:
            response = get_response(request)
            status_code = str(response.status_code)

            if response.status_code == 404:
                error_message = 'Page not found.'
            elif status_code.startswith('5') or status_code.startswith('4'):
                error_message = 'An unknown error occurred.'

            if error_message and not settings.MIDDLEWARE_DEBUG:
                status_code = response.status_code
                context = {
                    'error_message': error_message,
                    'status_code': status_code
                }
                return render(
                    request,
                    settings.DEFAULT_ERROR_TEMPLATE,
                    context=context,
                    status=status_code
                )

            return response

    return middleware
