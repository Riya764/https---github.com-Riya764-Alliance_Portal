''' MIS reporting admin '''
import math
import csv
from django import forms

from django.utils.encoding import force_text
from django.utils import timezone as dt
from django.utils.timezone import localtime
from django.conf.urls import url
from django.conf import settings
from django.contrib import admin
from django.core.paginator import Paginator
from django.template.response import TemplateResponse
from django.http import HttpResponse, JsonResponse

from app.models import RegionalDistributor
from .forms import AdvanceOrderFilterForm, RspLevelFilterForm, DatefieldsForm, RsLevelFilterForm, BasePackLevelForm, BillCountDataForm, SeLevelForm
from .models import AdvanceSearch, RspLevel, SeLevel, BasePackLevel,\
    BasepkLevelFormat, BillCount, RsLevel
from .sql import OrderAdvanceFilter, RspLevelFilter, SeLevelFilter, BasepkLevelFilter, BasepkLevelFormatFilter,\
    BillCountFilter, RsLevelFilter
from hul.constants import (ADMIN_PAGE_SIZE, LEADING_PAGE_RANGE_DISPLAYED,
                           TRAILING_PAGE_RANGE_DISPLAYED, LEADING_PAGE_RANGE,
                           TRAILING_PAGE_RANGE, NUM_PAGES_OUTSIDE_RANGE,
                           ADJACENT_PAGES)
from hul.choices import OrderStatus
from . import tasks


class AdvanceSearchAdmin(admin.ModelAdmin):
    ''' admin for advance search '''

    

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(AdvanceSearchAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(AdvanceSearchAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/advanced_filter.html'

        form = AdvanceOrderFilterForm()
        user = request.user

        if request.GET:
            form = AdvanceOrderFilterForm(request.GET)
            if form.is_valid():
                order_data = OrderAdvanceFilter.get_filtered_data(request.GET)
                if request.GET['order_type'] == OrderAdvanceFilter.ALIANCE_ORDER_QUERY:
                    ordertype_url = 'alliancepartnerorder'
                    ordertype = 'alliance'
                elif request.GET['order_type'] == OrderAdvanceFilter.DISTRIBUTOR_ORDER_QUERY:
                    ordertype_url = 'distributororder'
                    ordertype = 'distributor'

        if not user.is_superuser:
            
            if hasattr(user, 'regionaldistributor'):
                user_type = 'distributor'
                user_id = user.regionaldistributor.user_id
                form.fields['redistribution_stockist'].queryset = \
                    form.fields['redistribution_stockist'].queryset.filter(
                        user_id=user_id)
                form.fields['redistribution_stockist'].initial = [user_id]
                form.fields['redistribution_stockist'].to_field_name = 'user_id' 
                form.fields['redistribution_stockist'].widget.attrs['readonly'] = True
                form.fields['redistribution_stockist'].empty_label = None
                form.fields['brand'].queryset = \
                    RegionalDistributor.objects.filter(user=user_id).first().alliance_partner.all()

            if hasattr(user, 'alliancepartner'):
                user_type = 'alliance'
                user_id = user.alliancepartner.user_id
                form.fields['brand'].queryset = \
                    form.fields['brand'].queryset.filter(user_id=user_id)
                form.fields['brand'].initial = user_id
                form.fields['brand'].widget.attrs['readonly'] = True
                form.fields['brand'].empty_label = None

        query_set = {}
        total_count = 0
        pages = 0
        page = int(request.GET.get('page', 1))

        if order_data:
            paginator = Paginator(list(order_data), ADMIN_PAGE_SIZE)
            query_set = paginator.page(page)

            total_count = len(list(order_data))
            calculate = float(total_count) / float(ADMIN_PAGE_SIZE)
            pages = int(math.ceil(calculate))

        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()

        in_leading_range, in_trailing_range, pages_outside_leading_range,\
            pages_outside_trailing_range, page_range = \
            self.get_pages(pages, page)

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=query_set,
            total_count=total_count,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            pages=pages,
            page=page,
            page_range=page_range,
            in_leading_range=in_leading_range,
            in_trailing_range=in_trailing_range,
            pages_outside_leading_range=pages_outside_leading_range,
            pages_outside_trailing_range=pages_outside_trailing_range,
            get_params=get_params,
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        task = tasks.export_to_excel.delay(request.GET.urlencode(),
                                           request.GET['order_type'])
        return JsonResponse(task.id, safe=False)
    
    
    def get_pages(self, pages, page):
        in_leading_range = in_trailing_range = False
        pages_outside_leading_range = pages_outside_trailing_range = range(0)
        if pages <= LEADING_PAGE_RANGE_DISPLAYED + NUM_PAGES_OUTSIDE_RANGE + 1:
            in_leading_range = in_trailing_range = True
            page_range = [n for n in range(1, pages + 1)]
        elif page <= LEADING_PAGE_RANGE:
            in_leading_range = True
            page_range = [n for n in range(
                1, LEADING_PAGE_RANGE_DISPLAYED + 1)]
            pages_outside_leading_range = \
                [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        elif page > pages - TRAILING_PAGE_RANGE:
            in_trailing_range = True
            page_range = [n for n in range(pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, pages + 1)
                          if n > 0 and n <= pages]
            pages_outside_trailing_range = [
                n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
        else:
            page_range = [n for n in range(page - ADJACENT_PAGES, page + ADJACENT_PAGES + 1)
                          if n > 0 and n <= pages]
            pages_outside_leading_range = \
                [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
            pages_outside_trailing_range = [
                n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]

        return in_leading_range, in_trailing_range,\
            pages_outside_leading_range, pages_outside_trailing_range, page_range


class RspLevelAdmin(admin.ModelAdmin):
    ''' admin for advance search '''

    class Meta:
        verbose_name = 'RSP Level'
        verbose_name_plural = 'RSP Level'

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(RspLevelAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = eco_data = eco_count = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/rsplevel_filter.html'

        form = RspLevelFilterForm()
        user = request.user

        if request.GET:
            form = RspLevelFilterForm(request.GET)
            if form.is_valid():
                order_data, eco_data, eco_count = RspLevelFilter.get_filtered_data(
                    request.GET)

        if not user.is_superuser:
            if hasattr(user, 'regionaldistributor'):
                user_type = 'distributor'
                user_id = user.regionaldistributor.user_id
                form.fields['sales_promoter'].queryset = \
                    form.fields['sales_promoter'].queryset.filter(
                        regional_distributor__user_id=user_id)

            if hasattr(user, 'alliancepartner'):
                user_type = 'alliance'
                user_id = user.alliancepartner.user_id
                form.fields['sales_promoter'].queryset = \
                    form.fields['sales_promoter'].queryset.filter(
                        regional_distributor__alliance_partner__user_id=user_id)

        # moc_data =
        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()
        ordered_total_cost = dispatched_total_cost = total_grandtotal = 0
        ordered_shkti = dispatched_shkti = total_shkti = 0
        if order_data:
            ordered_total_cost = sum(
                map(lambda x: x['ordered'] or 0, order_data))
            dispatched_total_cost = sum(
                map(lambda x: x['dispatched'] or 0, order_data))
            total_grandtotal = sum(
                map(lambda x: x['grandtotal'] or 0, order_data))
        if eco_data:
            ordered_shkti = sum(map(lambda x: x['ordered'] or 0, eco_data))
            dispatched_shkti = sum(
                map(lambda x: x['dispatched']or 0, eco_data))
            total_shkti = len(eco_data)

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=order_data,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            get_params=get_params,
            eco_data=eco_data,
            eco_count=eco_count,
            ordered_total_cost=ordered_total_cost,
            total_grandtotal=total_grandtotal,
            dispatched_total_cost=dispatched_total_cost,
            total_shkti=total_shkti,
            dispatched_shkti=dispatched_shkti,
            ordered_shkti=ordered_shkti
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(RspLevelAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        response = RspLevel.get_csv_data(request)
        return response


class SeLevelAdmin(admin.ModelAdmin):
    ''' admin for SE Level search '''

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(SeLevelAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/selevel_filter.html'

        form = SeLevelForm()

        if request.GET:
            form = SeLevelForm(request.GET)
            if form.is_valid():
                order_data = SeLevelFilter.get_filtered_data(request.GET)

        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()
        total_cost = total_lines = 0
        if order_data:
            total_cost = sum(map(lambda x: x['tamount'] or 0, order_data))
            total_lines = sum(map(lambda x: x['lines'] or 0, order_data))

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=order_data,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            get_params=get_params,
            total_cost=total_cost,
            total_lines=total_lines

        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(SeLevelAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        order_data = SeLevelFilter.get_filtered_data(request.GET)
        filename = dt.datetime.today().strftime("%d%m%Y")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="SE Level Report %s.csv"' % filename

        writer = csv.writer(response)
        writer.writerow([
            'Shakti Entrepreneur Code',
            'Distributor',
            'RSP',
            'State',
            'MoC',
            'Ordered Amount',
            'Dispatched Amount',
            'Ordered Lines',
            'Dispatched Lines'
        ])

        for record in order_data:
            sp_name = ''
            if record['sales_promoter__regionalsalespromoter__rsp_id'] != None:
                sp_name = record['sales_promoter__regionalsalespromoter__rsp_id']

            writer.writerow([
                record['shakti_enterpreneur__shakti_user__code'],
                record['distributor__name'],
                sp_name,
                record['shipping_address__state__name'],
                record['moc_name'],
                record['ordered'] or 0,
                record['dispatched'] or 0,
                record['orderedlines'],
                record['dispatchedlines']
            ])

        total_cost = total_lines = 0
        if order_data:
            total_cost = sum(map(lambda x: x['tamount'] or 0, order_data))
            total_lines = sum(map(lambda x: x['lines'] or 0, order_data))

        writer.writerow([
            'Grand Total (Amount)',
            '',
            total_cost,
        ])

        writer.writerow([
            'Grand Total (lines)',
            '',
            total_lines
        ])

        return response


class BasePackLevelAdmin(admin.ModelAdmin):
    ''' admin for SE Level search '''

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(BasePackLevelAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/basepklevel_filter.html'

        form = BasePackLevelForm()

        if request.GET:
            form = BasePackLevelForm(request.GET)
            if form.is_valid():
                order_data = BasepkLevelFilter.get_filtered_data(request.GET)

        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()
        total_cost = 0
        if order_data:
            total_cost = sum(map(lambda x: x['grand_total'] or 0, order_data))

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=order_data,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            get_params=get_params,
            total_cost=total_cost
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(BasePackLevelAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        order_data = BasepkLevelFilter.get_filtered_data(request.GET)
        filename = dt.datetime.today().strftime("%d%m%Y")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Basepack Level Report %s.csv"' % filename

        writer = csv.writer(response)
        writer.writerow([
            'Base Pack Name',
            'Distributor',
            'RSP',
            'State',
            'MoC',
            'Ordered',
            'Dispatched'
            'Amount',

        ])

        for record in order_data:
            sp_name = ''
            if record['distributor_order__sales_promoter__regionalsalespromoter__rsp_id'] != None:
                sp_name = record['distributor_order__sales_promoter__regionalsalespromoter__rsp_id']

            writer.writerow([
                record['product__basepack_name'],
                record['distributor_order__distributor__name'],
                sp_name,
                record['shipping_address__state__name'],
                record['moc_name'],
                record['ordered_amount'],
                record['dispatched_amount'],
                record['grand_total']
            ])

        total_cost = 0
        if order_data:
            total_cost = sum(map(lambda x: x['grand_total'] or 0, order_data))

        writer.writerow([
            'Grand Total',
            '',
            '',
            total_cost
        ])

        return response


class BasepkLevelFormatAdmin(admin.ModelAdmin):
    ''' admin for SE Level search '''

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(BasepkLevelFormatAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/basepklevelformat_filter.html'

        form = DatefieldsForm()

        if request.GET:
            form = DatefieldsForm(request.GET)
            if form.is_valid():
                order_data = BasepkLevelFormatFilter.get_filtered_data(
                    request.GET)

        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()
        total_cost = 0
        if order_data:
            total_cost = sum(map(lambda x: x['tamount'] or 0, order_data))

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=order_data,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            get_params=get_params,
            total_cost=total_cost

        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(BasepkLevelFormatAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        order_data = BasepkLevelFormatFilter.get_filtered_data(request.GET)
        filename = dt.datetime.today().strftime("%d%m%Y")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Basepack Level Format Report %s.csv"' % filename

        writer = csv.writer(response)
        writer.writerow([
            'Base Pack Name',
            'Amount',

        ])

        for record in order_data:
            writer.writerow([
                record['product__basepack_name'],
                record['tamount']
            ])

        total_cost = 0
        if order_data:
            total_cost = sum(map(lambda x: x['tamount'] or 0, order_data))

        writer.writerow([
            'Grand Total',
            total_cost
        ])
        return response


class BillCountSearchAdmin(admin.ModelAdmin):
    ''' admin for SE Level search '''

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(BillCountSearchAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/billcount_filter.html'

        form = BillCountDataForm()

        if request.GET:
            form = BillCountDataForm(request.GET)
            if form.is_valid():
                order_data = BillCountFilter.get_filtered_data(request.GET)

        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()
        total_cost = total_lines = total_billcount = total_uniques = 0
        if order_data:
            total_cost = sum(map(lambda x: x['tamount'] or 0, order_data))
            total_lines = sum(map(lambda x: x['lines'] or 0, order_data))
            total_billcount = sum(
                map(lambda x: x['billcount'] or 0, order_data))
            total_uniques = sum(
                map(lambda x: x['unique_prd'] or 0, order_data))

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=order_data,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            get_params=get_params,
            total_cost=total_cost,
            total_lines=total_lines,
            total_billcount=total_billcount,
            total_uniques=total_uniques
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(BillCountSearchAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        order_data = BillCountFilter.get_filtered_data(request.GET)
        filename = dt.datetime.today().strftime("%d%m%Y")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Bill Count Report %s.csv"' % filename

        writer = csv.writer(response)
        writer.writerow([
            'Shakti Entrepreneur Code',
            'Distributor',
            'RSP',
            'State',
            'MoC',
            'Count of Bill No',
            'Ordered',
            'Dispatched',
            'Sum of Total Amount',
            'Total Lines',
            'Unique lines',

        ])

        for record in order_data:
            sale_name = ''
            if record['sales_promoter__regionalsalespromoter__rsp_id'] != None:
                sale_name = record['sales_promoter__regionalsalespromoter__rsp_id']
            writer.writerow([
                record['shakti_enterpreneur__shakti_user__code'],
                record['distributor__name'],
                sale_name,
                record['shipping_address__state__name'],
                record['moc_name'],
                record['billcount'],
                record['ordered_amount'],
                record['dispatched_amount'],
                record['tamount'],
                record['lines'],
                record['unique_prd']
            ])

        total_cost = total_lines = total_billcount = total_uniques = 0
        if order_data:
            total_cost = sum(map(lambda x: x['tamount'] or 0, order_data))
            total_lines = sum(map(lambda x: x['lines'] or 0, order_data))
            total_billcount = sum(
                map(lambda x: x['billcount'] or 0, order_data))
            total_uniques = sum(
                map(lambda x: x['unique_prd'] or 0, order_data))

        writer.writerow([
            'Grand Total',
            '',
            '',
            '',
            '',
            total_billcount,
            '',
            '',
            total_cost,
            total_lines,
            total_uniques
        ])
        return response


class RsLevelAdmin(admin.ModelAdmin):
    ''' admin for advance search '''

    class Meta:
        verbose_name = 'RS Level'
        verbose_name_plural = 'RS Level'

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(RsLevelAdmin, self).get_actions(request)
        if 'delete_selected' in actions.keys():
            del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        '''Advanced Order Filter'''
        order_data = eco_data = eco_count = None
        ordertype_url = ''
        ordertype = ''
        user_type = 'superuser'
        template = 'admin/misreporting/rslevel_filter.html'

        form = RsLevelFilterForm()
        user = request.user

        if request.GET:
            form = RsLevelFilterForm(request.GET)

            if form.is_valid():
                order_data, eco_data, eco_count = RsLevelFilter.get_filtered_data(
                    request.GET)

        if not user.is_superuser:
            if hasattr(user, 'regionaldistributor'):
                user_type = 'distributor'
                user_id = user.regionaldistributor.user_id
                form.fields['redistribution_stockist'].queryset = \
                    form.fields['redistribution_stockist'].queryset.filter(
                        alliance_partner__user_id=user_id)

            if hasattr(user, 'alliancepartner'):
                user_type = 'alliance'
                user_id = user.alliancepartner.user_id
                form.fields['redistribution_stockist'].queryset = \
                    form.fields['redistribution_stockist'].queryset.filter(
                        alliance_partner__user_id=user_id)

        # moc_data =
        context = self.admin_site.each_context(request)
        opts = self.model._meta
        title = opts.verbose_name.title()

        params = request.GET.copy()
        if 'page' in params:
            del params['page']

        get_params = params.urlencode()
        ordered_total_cost = dispatched_total_cost = total_grandtotal = 0
        ordered_shkti = dispatched_shkti = total_shkti = 0
        if order_data:
            ordered_total_cost = sum(
                map(lambda x: x['ordered'] or 0, order_data))
            dispatched_total_cost = sum(
                map(lambda x: x['dispatched'] or 0, order_data))
            total_grandtotal = sum(
                map(lambda x: x['grandtotal'] or 0, order_data))
        if eco_data:
            ordered_shkti = sum(map(lambda x: x['ordered'] or 0, eco_data))
            dispatched_shkti = sum(
                map(lambda x: x['dispatched'] or 0, eco_data))
            total_shkti = len(eco_data)

        context = dict(
            self.admin_site.each_context(request),
            module_name=force_text(opts.verbose_name_plural),
            title=title,
            is_popup=False,
            to_field='',
            cl=self,
            opts=self.opts,
            action_form=form,
            form=form,
            url=ordertype_url,
            ordertype=ordertype,
            usertype=user_type,
            data=order_data,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
            get_params=get_params,
            eco_data=eco_data,
            eco_count=eco_count,
            ordered_total_cost=ordered_total_cost,
            total_grandtotal=total_grandtotal,
            dispatched_total_cost=dispatched_total_cost,
            total_shkti=total_shkti,
            dispatched_shkti=dispatched_shkti,
            ordered_shkti=ordered_shkti
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            template,
            context,
        )

    def get_urls(self):
        '''
        append custom url
        '''
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super(RsLevelAdmin, self).get_urls()
        custom_urls = [
            url(r'^download-csv/$', self.admin_site.admin_view(self.download_csv),
                name='%s_%s_download_csv' % info)
        ]

        return custom_urls + urls

    def download_csv(self, request, *args, **kwargs):
        '''
        create csv data and force download
        '''
        response = RsLevel.get_csv_data(request)
        return response


admin.site.register(AdvanceSearch, AdvanceSearchAdmin)
admin.site.register(RspLevel, RspLevelAdmin)
admin.site.register(SeLevel, SeLevelAdmin)
admin.site.register(BasePackLevel, BasePackLevelAdmin)
# admin.site.register(BasepkLevelFormat, BasepkLevelFormatAdmin)
admin.site.register(BillCount, BillCountSearchAdmin)
admin.site.register(RsLevel, RsLevelAdmin)
