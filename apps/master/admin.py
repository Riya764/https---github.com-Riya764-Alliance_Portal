'''master/admin.py'''
from django.contrib import admin
from master.models import Country

# Register your models here.
class CountryAdmin(admin.ModelAdmin):
    """
    custom Admin Class for Privacy model
    """
    list_display = ['name', 'country_code', 'phone_code']
    search_fields = ['name', 'country_code', 'phone_code']
    list_per_page = 20

#admin.site.register(Country, CountryAdmin)
