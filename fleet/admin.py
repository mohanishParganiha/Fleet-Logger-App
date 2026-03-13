
from django.contrib import admin
from .models import Driver, Vehicle, TripLog


class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number',
                    'user', 'status', 'date_created')
    list_filter = ('status',)
    search_fields = ('name', 'license_number', 'user__email')
    fields = ('user', 'name', 'license_number', 'status')


admin.site.register(Driver)
