from django.contrib import admin
from .models import CustomUser, Subscription


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('first_name', 'email')


admin.site.register(Subscription)
