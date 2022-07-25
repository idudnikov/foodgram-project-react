from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Subscription


class CustomUserAdmin(UserAdmin):
    list_display = [
        "email",
        "username",
    ]
    list_filter = [
        "email",
        "username",
    ]


admin.site.register(Subscription)
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
