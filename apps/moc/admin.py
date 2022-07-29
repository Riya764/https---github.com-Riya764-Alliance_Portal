from django.contrib import admin

# Register your models here.
from moc.models import MoCMonth, MoCYear


class MoCMonthInline(admin.TabularInline):
    '''Tabular Inline View for MoCMonth'''

    model = MoCMonth
    min_num = 3
    extra = 0
    readonly_fields = ('name', 'start_date', 'end_date')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class MoCMonthAdmin(admin.ModelAdmin):
    list_display = ('name', 'moc_year', 'start_date', 'end_date', )
    date_hierarchy = ('start_date')
    readonly_fields = ('start_date', 'end_date', 'moc_year')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(MoCMonthAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


class MoCYearAdmin(admin.ModelAdmin):
    fields = ('year', 'name')
    list_display = ('name', 'year')
    readonly_fields = ('name', 'year')
    inlines = [MoCMonthInline]

    def get_actions(self, request):
        actions = super(MoCYearAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(MoCYearAdmin, self).get_queryset(request)
        queryset = queryset.order_by('year')  # TODO
        return queryset


admin.site.register(MoCYear, MoCYearAdmin)
admin.site.register(MoCMonth, MoCMonthAdmin)
