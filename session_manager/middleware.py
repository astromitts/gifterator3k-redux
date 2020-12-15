from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.urls import resolve, reverse
from django.urls.exceptions import Resolver404


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

        except Resolver404:
            if not settings.MIDDLEWARE_DEBUG:
                error_message = 'Page not found.'
                status_code = 404

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
