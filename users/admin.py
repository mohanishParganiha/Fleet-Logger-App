from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_admin',
                    'is_staff', 'date_created', 'date_updated')

    list_filter = ('is_admin', 'is_staff', 'is_active')

    readonly_fields = ('date_created', 'date_updated')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username',)}),
        ('Permissions', {'fields': (
            'is_admin', 'is_staff', 'is_active',
            'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('date_created', 'date_updated')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    search_fields = ('email', 'username')

    ordering = ('email',)

    filter_horizontal = ('groups', 'user_permissions')


admin.site.register(User, UserAdmin)
