from django.contrib import admin

from session_manager.models import UserToken, EmailLog, AppUser

class UserTokenAdmin(admin.ModelAdmin):
    fields = [
        'appuser',
        'token',
        'token_type',
        'expiration',
        'link',
    ]
    readonly_fields = ['link', ]

admin.site.register(UserToken, UserTokenAdmin)
admin.site.register(EmailLog)
admin.site.register(AppUser)
