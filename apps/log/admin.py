'''LOG'''
from django.contrib import admin
from django.conf import settings
from django.forms import TextInput, Textarea
from django.db import models
from django.contrib.admin import SimpleListFilter
from hul.utility import CustomAdminTitle
from .models import Log

class NullListFilter(SimpleListFilter):
    '''Null List Filter'''
    @classmethod
    def lookups(cls, request, model_admin):
        return (
            ('1', 'Success',),
            ('0', 'Execption',),
        )

    def queryset(self, request, queryset):
        if self.value() in ('0', '1'):
            kwargs = {
                '{0}__isnull'.format(self.parameter_name): self.value() == '1'}
            return queryset.filter(**kwargs)
        return queryset


def null_filter(field, title_=None):
    '''null filter'''
    class NullListFieldFilter(NullListFilter):
        '''null list filter'''
        parameter_name = field
        title = title_ or parameter_name
    return NullListFieldFilter


class LogAdmin(CustomAdminTitle):
    '''Log Admin'''
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 20})},
    }

    your_fields = Log._meta.local_fields
    lst_of_field_names = [f.name for f in your_fields]
    lst_of_field_names.remove('request_content')
    lst_of_field_names.remove('response_content')
    list_display = ['method_type', 'method_name', 'short_request_content',
                    'short_response_content', 'full_stack_trace', 'total_time_taken']
    list_per_page = 500
    list_filter = ('response_status_type', 'method_type',
                   null_filter('exception_full_stack_trace'),)

if settings.DEBUG:
    admin.site.register(Log, LogAdmin)
