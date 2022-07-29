''' pdp/admin.py '''
from urlparse import urlparse
from django.contrib import admin
from django.utils import timezone as dt
from datetime import timedelta, datetime

from hul.utility import NoAdminTitle, HulUtility
from pdp.models import TodayRS, TodayShakti


class TodayShaktiAdmin(NoAdminTitle):

    model = TodayShakti

    list_display = ['user', 'code', 'beat_name', 'order_day', 'regional_sales',
                    'address', 'min_order', 'get_order_count', 'thumbnail']
    list_select_related = [
        'regional_sales', 'user', 'address', 'address__state',
        'address__country', 'user__shakti_user', 'regional_sales__user',]
    list_display_links = None
    readonly_fields = ('get_order_count',)
    list_filter = ('order_day', )

    def changelist_view(self, request, extra_context=None):

        referer = request.META.get('HTTP_REFERER', '')
        path = urlparse(referer)
        if path:
            path = path.path
        current_path = request.path

        if path != current_path:
            if not request.GET.has_key('order_day__exact'):
                current_day = dt.datetime.today().isoweekday()
                q = request.GET.copy()
                q['order_day__exact'] = current_day + 1
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()

        return super(TodayShaktiAdmin, self).changelist_view(request,
                                                             extra_context=extra_context)

    def has_add_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        '''Remove object delete permissions'''
        actions = super(TodayShaktiAdmin, self).get_actions(request)
        del actions['delete_selected']

        return actions

    def get_order_count(self, obj=None):
        ''' get order counts for current week '''
        week_range = HulUtility.week_range(dt.datetime.now())
        order_count = obj.user.do_shaktientrepreneur_related.filter(
            created__range=week_range).count()

        return order_count
    get_order_count.short_description = 'Orders this week'


class TodayRSAdmin(NoAdminTitle):

    model = TodayRS

    list_display = ['user', 'code',  'order_day', 'address',
                    'min_order', 'thumbnail']
    list_select_related = ['user']
    list_display_links = None
    list_filter = ('order_day', )

    def changelist_view(self, request, extra_context=None):

        referer = request.META.get('HTTP_REFERER', '')
        path = urlparse(referer)
        if path:
            path = path.path
        current_path = request.path

        if path != current_path:
            if not request.GET.has_key('order_day__exact'):
                current_day = dt.datetime.today().isoweekday()
                q = request.GET.copy()
                q['order_day__exact'] = current_day + 1
                request.GET = q
                request.META['QUERY_STRING'] = request.GET.urlencode()

        return super(TodayRSAdmin, self).changelist_view(
            request,
            extra_context=extra_context)

    def has_add_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        '''Remove object delete permissions'''
        actions = super(TodayRSAdmin, self).get_actions(request)
        del actions['delete_selected']

        return actions


admin.site.register(TodayShakti, TodayShaktiAdmin)
admin.site.register(TodayRS, TodayRSAdmin)
