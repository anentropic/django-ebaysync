from django.contrib import admin

from .models import UserToken


class UserTokenAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserToken, UserTokenAdmin)