'''order/admin.py'''
from django.contrib import admin
from django.conf import settings
from localization.models import State, MeasurementUnit
from hul.constants import ADMIN_PAGE_SIZE
from hul.utility import CustomAdminTitle


class CountryAdmin(CustomAdminTitle):
    """
    custom Admin Class for Privacy model
    """
    list_display = ['name', 'country_code', 'phone_code']
    search_fields = ['name', 'country_code', 'phone_code']
    list_per_page = ADMIN_PAGE_SIZE

    def has_delete_permission(self, request, obj=None):
        return False

class StateAdmin(CustomAdminTitle):
    """
    custom Admin Class for Privacy model
    """
    list_display = ['name', 'country',]
    search_fields = ['name', 'country__name',]
    list_filter = ['country__name']
    list_per_page = ADMIN_PAGE_SIZE

    def has_delete_permission(self, request, obj=None):
        return False

class CityAdmin(CustomAdminTitle):
    """
    custom Admin Class for Privacy model
    """
    list_display = ['name', 'state', 'country']
    search_fields = ['name', 'state__name', 'country__name']
    list_filter = ['state__name', 'country__name']
    list_per_page = ADMIN_PAGE_SIZE

    def has_delete_permission(self, request, obj=None):
        return False

class MeasurementUnitAdmin(CustomAdminTitle):
    """
    custom Admin Class for Privacy model
    """
    list_display = ['unit', 'is_active', 'created']
    search_fields = ['unit', ]
    list_per_page = ADMIN_PAGE_SIZE

    def has_delete_permission(self, request, obj=None):
        return False

if settings.DEBUG:
    admin.site.register(State, StateAdmin)
    admin.site.register(MeasurementUnit, MeasurementUnitAdmin)
