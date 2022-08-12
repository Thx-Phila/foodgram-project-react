from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class UserAdmin(UserAdmin):
    list_filter = ('username', 'email',)


admin.site.register(User, UserAdmin)
