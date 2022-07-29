# -*- coding: utf-8 -*-
''' orders/admin.py '''
from django.contrib import admin
import math
import csv
import tablib
from pytz import timezone
from datetime import date
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect

from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import localtime
from django.utils.html import format_html
from django.utils import timezone as dt

from django.db.models import Sum, CharField, IntegerField, Value as V, F, Func
from django.db.models.functions import Concat
from django.template.response import TemplateResponse

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
from django.conf.urls import url

from easy_pdf.rendering import render_to_pdf_response
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from app.models import UserAddress
from hul.utility import CustomAdminTitle
from hul.constants import (ADMIN_PAGE_SIZE, LEADING_PAGE_RANGE_DISPLAYED,
                           TRAILING_PAGE_RANGE_DISPLAYED, LEADING_PAGE_RANGE,
                           TRAILING_PAGE_RANGE, NUM_PAGES_OUTSIDE_RANGE,
                           ADJACENT_PAGES, DISPATCH_DAYS)
from hul.choices import OrderStatus
from hul.settings.common import ADMIN_SITE_HEADER
# from hul.sqllib import Cast, LPad, MCharField
from localization.models import State, Country
from orders.lib.order_management import OrderManagement
from orders.lib.order_management import CalculatePrice
from orders.lib.create_distributor_order import DispatchDistributorOrder
from .models import (DistributorOrder, DistributorOrderDetail,
                     AlliancePartnerOrder, AlliancePartnerOrderDetail,
                     DistributorStock, AlliancePartnerDistributorOrder,
                     ReviewPrimaryOrder, ReviewPrimaryOrderDetail)
from .forms import (DistributorOrderAdminForm,
                    AllianceOrderAdminForm, DistributorOrderDetailAdminForm)
from .invoices import DistributorInvoice
from app.models import (
    AlliancePartner, ShaktiEntrepreneur, RegionalDistributor)

from .filters import AllianceFilter, DistributorFilter, OrderStatusFilter, PromoterFilter, SecondaryOrderStatusFilter


# constant for updating user action on order before a given date for this case 20-sep-2020
from datetime import datetime
#date_val = '20-09-2020'
date_val = '20-09-2025'

UPDATE_DATE = datetime.strptime(date_val, '%d-%m-%Y')


def remove_from_fieldsets(fieldsets, fields):
    '''
    funtion to remove field from a fieldset
    '''
    for fieldset in fieldsets:
        for field in fields:
            if field in fieldset[1]['fields']:
                newfields = _get_fields(fieldset[1]['fields'], fields)
                fieldset[1]['fields'] = tuple(newfields)
                break


def _get_fields(current_fields, fields):
    newfields = []
    for myfield in current_fields:
        if not myfield in fields:
            newfields.append(myfield)
    return newfields


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


class DistributorOrderDetailInline(admin.TabularInline):
    ''' Distributor Orders Detail Inline '''
    model = DistributorOrderDetail
    form = DistributorOrderDetailAdminForm
    min_num = 0
    max_num = 2
    extra = 0
    fields = ('product', 'get_cases', 'get_units',
              'get_dispatch_cases', 'get_dispatch_units', 'returned_units','unitprice',
              'price', 'discount_amount', 'distributor_discount',
              'cgst', 'sgst', 'igst', 'net_amount',
              'is_free', 'item_status', 'promotion_applied', 'get_hsn_code')
    readonly_fields = ['get_order_type', 'get_cases', 'get_units',
                       'get_dispatch_units', 'get_dispatch_cases', 'get_hsn_code']

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return False

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_order_type(self, obj):
        '''
        get type of order whether unit or cld
        '''
        return_str = 'Unit'
        if obj.is_cld:
            return_str = 'CLD'
        return return_str
    get_order_type.short_description = 'Type'

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj:
            for field in self.opts.local_fields:
                if field.name not in readony_list and field.name not in ['item_status']:
                    readony_list.append(field.name)
            if UPDATE_DATE.date() < date.today():
                readony_list.extend(['item_status'])

            if request.user.is_superuser:
                readony_list.extend(['item_status'])
        return readony_list

    def get_queryset(self, request):
        ''' adding related with queryset '''
        queryset = super(DistributorOrderDetailInline, self).get_queryset(request).\
            select_related('shipping_address', 'product',
                           'shipping_address__state', 'shipping_address__country', 'product')
        return queryset


class DistributorOrderAdmin(CustomAdminTitle):
    ''' Distributor Orders options '''
    
    # def get_form(self, request, obj=None, **kwargs):
    #     if obj.order_status != 5:
    #         print("****************************************8s")
    #         kwargs.update({
    #             'exclude': getattr(kwargs, 'exclude', tuple()) + ('return_order',),
    #         })
    #     return super(DistributorOrderAdmin, self).get_form(request, obj, **kwargs)
    form = DistributorOrderAdminForm
    # def get_fields(self, request, obj=None):
    #     print("*************************")
    #     fields = super(DistributorOrderAdmin, self).get_fields(request, obj)
    #     if obj.order_status != 5:
    #         fields.remove('return_order')
    #     return fields

    inlines = [DistributorOrderDetailInline]
    model = DistributorOrder
    fieldsets = (
        (None, {
            'fields': ('distributor', 'sales_promoter',
                       'shakti_enterpreneur', 'get_shakti_code',
                       'shipping_address'),
            'classes': ('cols-2',)
        }),
        (None, {
            'fields': ('order_status', 'payment_status', 'cancel_order', 'cancel_reason'),
            'classes': ('cols-2',)
        }),
        (None, {
            'fields': ('amount', 'discount_amount', 'tax', 'total_amount', 'invoice_number', 'get_gst_code'),
            'classes': ('cols-2',)
        }),
         (None,{
            'fields':('return_order',)
        }),
        (None,{
            'fields':('product','return_units',)
        })
    )
    

    list_per_page = ADMIN_PAGE_SIZE
    list_display = ['get_order_id', 'distributor', 'get_rsp_id',
                    'get_se_hul_code', 'get_order_date', 'dispatched_on',
                    'total_amount',
                    'order_status', 'payment_status', 'order_actions', 'moc']
    search_fields = ['id', 'distributor__name',
                     'sales_promoter__username', 'invoice_number']
    list_filter = (('modified', DateRangeFilter), SecondaryOrderStatusFilter, ('dispatched_on', DateRangeFilter),  PromoterFilter,
                   )
    change_list_template = "admin/orders/change_list.html"

    change_form_template = "admin/orders/change_form.html"


    actions = ['dispatch_order',
               'generate_invoice', 'export_order_list', 'export_orders']
    readonly_fields = ['get_shakti_code', 'get_gst_code']
    list_select_related = [
        'distributor', 'sales_promoter', 'shakti_enterpreneur__shakti_user', 'shipping_address', 'moc',
        'shipping_address__state', 'shipping_address__country'
    ]

    def export_order_list(self, request, queryset):
        data_headers = ['ORDER ID', 'REDISTRIBUTION STOCKIST', 'RS_PIL_CODE', 'RSP', 'SHAKTI ENTERPRENEUR', 'SHAKTI ENTERPRENEUR CODE', 'ORDERED DATE',
                        'DISPATCHED ON', 'TOTAL AMOUNT', 'ORDER STATUS', 'PAYMENT STATUS', 'MOC', 'PRODUCT', 'PRODUCT CODE', 'BASEPACK CODE',
                        'ORDERED UNITS', 'DISPATCH UNITS', 'BASE RATE',
                        'DISCOUNT AMOUNT', 'DISTRIBUTOR DISCOUNT', 'CGST', 'SGST', 'IGST', 'NET AMOUNT', 'ITEM STATUS', 'PROMOTION APPLIED']
        data = tablib.Dataset(headers=data_headers, title='Orders')

        for order in queryset:
            order_details = order.distributor_order_details.all()
            dispatch_date = str(order.dispatched_on.date()
                                ) if order.dispatched_on else ''
            for order_detail in order_details:
                dispatch_qty = order_detail.dispatch_quantity or 0
                row = (order.pk, str(order.distributor), str(order.distributor.regionaldistributor.code), str(order.sales_promoter), str(order.shakti_enterpreneur), str(order.shakti_enterpreneur.username),
                       str(order.created.date(
                       )), dispatch_date, order_detail.net_amount, order.get_order_status_display(),
                       order.get_payment_status_display(), order.get_moc_name(), str(
                           order_detail.product), order_detail.product_id, order_detail.product.basepack_code, order_detail.quantity,
                       dispatch_qty, order_detail.unitprice, order_detail.discount_amount, order_detail.distributor_discount,
                       order_detail.cgst, order_detail.sgst, order_detail.igst, order_detail.net_amount,
                       order_detail.get_item_status_display(), order_detail.promotion_applied)
                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="order_item.xls"'
        response.write(data.export('xls'))
        return response
    export_order_list.short_description = 'Export order item '

    def export_orders(self, request, queryset):
        data_headers = ['ORDER ID', 'INVOICE NUMBER', 'REDISTRIBUTION STOCKIST', 'RS_PIL_CODE', 'RSP', 'SHAKTI ENTERPRENEUR', 'SHAKTI ENTERPRENEUR CODE', 'ORDERED DATE',
                        'DISPATCHED ON', 'TOTAL AMOUNT', 'TAX ', 'DISCOUNT AMOUNT', 'GROSS AMOUNT', 'ORDER STATUS', 'PAYMENT STATUS', 'MOC']

        data = tablib.Dataset(headers=data_headers, title='Orders')
        for order in queryset:
            dispatch_date = str(order.dispatched_on.date()
                                ) if order.dispatched_on else ''
            row = (order.pk, str(order.invoice_number), str(order.distributor), str(order.distributor.regionaldistributor.code),
                   str(order.sales_promoter), str(order.shakti_enterpreneur),
                   str(order.shakti_enterpreneur.username), str(
                       order.created.date()), dispatch_date,
                   order.total_amount, order.tax, order.discount_amount, order.amount, order.get_order_status_display(),
                   order.get_payment_status_display(), order.get_moc_name())

            data.append(tuple(row))
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="orders.xls"'
        response.write(data.export('xls'))
        return response
    export_orders.short_description = 'Export Orders'

    class Media:
        '''
        adding custom media to admin
        '''
        js = ('admin/orders/js/order_management.js',
              'admin/orders/js/orders.js?v=1')
        css = {
            'all': ('admin/orders/css/order_management.css',)
        }

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Order items'
        kwargs['extra_context']['download_title'] = 'Download Invoice'
        return super(DistributorOrderAdmin, self).changelist_view(*args, **kwargs)

    @classmethod
    def order_actions(cls, obj):
        '''
        Order Action dispatch order/View Invoice
        '''
        html = 'N/A'
        if UPDATE_DATE.date() < obj.created.date():
            html = format_html('<p> No Action Allowed </p>')
        elif obj.order_status == OrderStatus.ORDERED and dt.now() - obj.created:
            html = format_html('<a href="{}"> Dispatch </a>',
                               reverse('dispatch_stockist_order', args=[obj.pk]))
        if obj.order_status in [OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
            html = format_html('<a target="_blank" href="{}"> View Invoice </a>',
                               reverse('distributer-order-invoice',
                                       args=[obj.pk])
                               )
        return html

    def dispatch_order(self, request, queryset):
        '''
        Custom admin action, an intermediate page will be displayed
        with respective order details
        '''

        orders = queryset.filter(order_status=OrderStatus.ORDERED)
        from django.contrib import messages
        # for order in orders:
        #     if (dt.now() - order.created).days > DISPATCH_DAYS:
        #         messages.error(request, 'Can not dispatch order older than 15 days.')
        #         return
        # blank orders
        if orders:
            dispatch_obj = DispatchDistributorOrder(orders)
            ignore_orders, dispatched_orders = dispatch_obj.create_dispatch_orders()

            # if not ignore_orders and not dispatched_orders:
            #     messages.warning(
            #         request, 'Selected Order(s) are not dispatched, please check closing stock for the products.')

            # if ignore_orders:
            #     messages.warning(
            #         request, 'Order(s) {orders} are not dispatched, please check closing stock for the products.'.format(orders=', '.join(ignore_orders)))

            if dispatched_orders:
                messages.success(
                    request, 'Order(s) {orders} have been dispatched successfully.'.format(orders=', '.join(dispatched_orders)))
        else:
            messages.warning(
                request, 'Select Order(s) with order status {}.'.format(OrderStatus.LABEL[OrderStatus.ORDERED]))

        return HttpResponseRedirect(request.build_absolute_uri())

    dispatch_order.short_description = "Dispatch Orders"

    def get_final_stock(self, post_data):
        final_stock = {}
        for key in post_data.keys():
            if key.startswith('final_stock'):
                product_stock = {}
                product_id = int(key.split('_')[-1])
                if product_id not in product_stock:
                    final_stock.update({product_id: 0})
                final_stock[product_id] = int(post_data[key])

        return final_stock

    def generate_invoice(self, request, queryset):
        '''
        Custom admin action, for generating invoices
        '''
        order_ids = []
        shakti_ids = []
        shakti_wise_orders = {}
        invoice_obj = DistributorInvoice()
        queryset = queryset.filter(
            order_status__in=[OrderStatus.DISPATCHED, OrderStatus.DELIVERED])\
            .prefetch_related('distributor_order_details')

        for obj in queryset:
            order_ids.append(obj)
            shakti_enterpreneur_id = obj.shakti_enterpreneur_id

            if shakti_enterpreneur_id not in shakti_ids:
                shakti_ids.append(shakti_enterpreneur_id)
                invoice_obj.prepare_shakti_wise(shakti_wise_orders, obj)
            shakti_wise_orders[shakti_enterpreneur_id]['total_amount'] += obj.total_amount
            shakti_wise_orders[shakti_enterpreneur_id]['total_quantity'] += obj.get_total_quantity()

        orderlines = list(DistributorOrderDetail.objects.filter(
            distributor_order__in=order_ids).
            select_related('distributor_order', 'distributor_order__distributor',
                           'product', 'product__brand',
                           'product__brand__user'
                           )
        )

        if orderlines:
            shakti_individual_orders, sku_orders, gross_amount = \
                invoice_obj.prepare_individual_sku_orders(queryset, orderlines)

            context = {
                'site_title': _(ADMIN_SITE_HEADER),
                'queryset': queryset,
                'shakti_individual_orders': shakti_individual_orders,
                'shakti_wise_orders': list(shakti_wise_orders.values()),
                'sku_orders': sku_orders,
                'gross_amount': gross_amount
            }

            template = 'admin/orders/generate_invoice.html'
            date = dt.datetime.today().strftime("%d_%m_%Y")
            filename = 'invoice_' + date + '.pdf'
            return render_to_pdf_response(
                request,
                template,
                context,
                filename=filename,
                content_type='application/pdf')
        else:
            messages.error(
                request, 'Please select order(s) with status Dispatched or Delivered.')
            return HttpResponseRedirect(request.build_absolute_uri())

    generate_invoice.short_description = "Download Invoice"

    def get_order_id(self, obj):
        '''
        generate order id for rsp
        '''
        return 'RSP%s' % str(obj.pk).zfill(6)
    get_order_id.short_description = 'Order ID'

    def get_gst_code(self, obj):
        return obj.distributor.regionaldistributor.gst_code
    get_gst_code.short_description = 'Gst Code'

    def get_rsp_id(self, obj):
        '''
        generate order id for rsp
        '''
        return obj.sales_promoter.regionalsalespromoter.rsp_id
    get_rsp_id.short_description = 'RSP'

    def get_se_hul_code(self, obj):
        '''
        generate order id for rsp
        '''
        return obj.shakti_enterpreneur.shakti_user.code
    get_se_hul_code.short_description = 'Shakti Enterpreneur'

    def get_shakti_code(self, obj):
        '''
        get shakti code for order details
        '''
        shakti_details = ShaktiEntrepreneur.objects.values(
            'code').filter(user_id=obj.shakti_enterpreneur.pk).first()
        return shakti_details['code']
    get_shakti_code.short_description = 'Shakti Enterpreneur Code'

    def get_order_date(self, obj):
        ''' changed short description '''
        return obj.created
    get_order_date.short_description = "Ordered Date"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def get_actions(self, request):
        actions = super(DistributorOrderAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def get_queryset(self, request):
        queryset = super(DistributorOrderAdmin, self).get_queryset(request).\
            select_related('distributor', 'sales_promoter',
                           'shakti_enterpreneur', 'shipping_address')
        if not request.user.is_superuser:
            queryset = queryset.filter(distributor=request.user)
        return queryset

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            remove_from_fieldsets(self.fieldsets, ('distributor',))
        # remove_from_fieldsets(self.fieldsets, ('return_order',))
        # if obj.order_status == 5:
        #     print("****************************************8s")
            
        #     # self.exclude=('return_order',)
        #     self.fieldsets+=((None, {'fields': ('return_order',),}),)
            # remove_from_fieldsets(self.fieldsets, ('return_order',))
        # else:ssssssssssssssss
           
        #    self.fieldsets+=((None, {'fields': ('return_order',),}),)

            

        return super(DistributorOrderAdmin, self).get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj:
            for field in self.opts.local_fields:
                if field.name not in readony_list and \
                   field.name not in ['order_status', 'payment_status',
                                      'cancel_order', 'cancel_reason']:
                    readony_list.append(field.name)
            if obj.order_status == OrderStatus.CANCELLED:
                readony_list.extend(['payment_status',
                                     'cancel_order', 'cancel_reason'])
            if request.user.is_superuser:
                readony_list.extend(['order_status', 'payment_status',
                                     'cancel_order', 'cancel_reason'])
        return readony_list

    def get_list_display(self, request):
        default_list_display = super(
            DistributorOrderAdmin, self).get_list_display(request)
        if not request.user.is_superuser:
            lst = list(default_list_display)
            lst.remove('distributor')
            return tuple(lst)
        return default_list_display

    def response_change(self, request, obj):
        ''' redirecting after saving order '''
        if obj.order_status == OrderStatus.DISPATCHED:
            return HttpResponseRedirect(reverse('dispatch_stockist_order',
                                                kwargs={'order_id': obj.id}))
        else:
            return super(DistributorOrderAdmin, self).response_change(request, obj)

    def save_model(self, request, obj, form, change):
        ''' override save model for redirecting to dispatch page '''
        product = form.cleaned_data.get('product', None)
        # price = form.cleaned_data.get('price', None)
        return_units = form.cleaned_data.get('return_units', None)
        # distributor=self.cleaned_data.get('distributor0')
        # print(product)
        distributor_order=DistributorOrderDetail.objects.filter(product__basepack_name=product,distributor_order_id=obj.id).order_by('-id')
        
        new_quantity=distributor_order[0].dispatch_quantity
        new_quantity-=return_units
        if new_quantity==0:
            new_status=OrderStatus.RETURNED
        else:
            new_status=OrderStatus.PARTIAL_RETURN
        distributor_order.update(returned_units=return_units,dispatch_quantity=new_quantity, item_status=new_status)
        reg=DistributorStock.objects.filter(product__basepack_name=product,distributor_id=obj.distributor).order_by('-id')
        value= reg[0].closing_stock+return_units
        # print(ordered_units)
        reg.update(closing_stock=value)
        if change and obj.order_status != OrderStatus.DISPATCHED:
            super(DistributorOrderAdmin, self).save_model(
                request, obj, form, change)


    def save_formset(self, request, form, formsets, change):
        ''' avoid save related if status is dispatch '''

        if change and form.instance.order_status != OrderStatus.DISPATCHED:
            super(DistributorOrderAdmin, self).save_formset(
                request, form, formsets, change)
        else:
            instances = formsets.save(commit=False)
            for instance in instances:
                old_value = DistributorOrderDetail.objects.values(
                    'item_status').get(pk=instance.pk)
                instance.item_status = old_value['item_status']
                instance.save()


class AllianceDistributorDetailInline(admin.TabularInline):
    ''' Alliance Partner Distributor Orders Detail Inline '''
    model = AlliancePartnerDistributorOrder
    form = AllianceOrderAdminForm
    min_num = 0
    max_num = 0
    extra = 0
    readonly_fields = ('get_cases', 'get_units',
                       'get_dispatch_cases', 'get_dispatch_units')
    fields = ('get_distributor', 'product', 'get_cases', 'get_units',
              'get_dispatch_cases', 'get_dispatch_units', 'unitprice', 'price',
              'item_status')

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return False

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_distributor(self, obj):
        ''' get distributor of the order '''
        return obj.alliance_partner_order.distributor
    get_distributor.short_description = 'Redistribution Stockist'

    def get_queryset(self, request):
        queryset = super(AllianceDistributorDetailInline, self).get_queryset(request).\
            select_related('product', 'alliance_partner_order', 'shipping_address__country',
                           'shipping_address__state',
                           ).filter(distributor_order_detail__isnull=True)
        return queryset

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj is not None:
            for field in self.fields:
                if field not in readony_list and field != 'item_status':
                    readony_list.append(field)
            if request.user.is_superuser:
                readony_list.extend(['item_status'])
        return readony_list


class AlliancePartnerDetailInline(admin.TabularInline):
    ''' Distributor Orders Detail Inline '''
    model = AlliancePartnerOrderDetail
    form = AllianceOrderAdminForm
    fields = []
    min_num = 0
    max_num = 0
    extra = 0
    readonly_fields = ('get_cases', 'get_units',
                       'get_dispatch_units', 'get_net_amount', 'get_dispatch_cases')
    fields = ('id', 'invoice_number_alliance', 'product', 'get_cases', 'get_units',
              'get_dispatch_cases', 'get_dispatch_units', 'unitprice', 'price', 'discount_amount',
              'cgst_amount', 'sgst_amount', 'igst_amount', 'get_net_amount', 'item_status',)

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return False

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_queryset(self, request):
        queryset = super(AlliancePartnerDetailInline, self).get_queryset(request).\
            select_related('product', 'alliance_partner_order')

        return queryset

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj is not None:
            for field in self.opts.local_fields:
                if field.name not in readony_list and field.name != 'item_status':
                    readony_list.append(field.name)
            if request.user.is_superuser or hasattr(request.user, 'alliancepartner'):
                readony_list.extend(['item_status'])
        return readony_list

    def get_net_amount(self, obj=None):
        '''
        return price + taxes
        '''
        if obj:
            return (obj.price or 0.0) - obj.discount_amount + (obj.cgst_amount or 0.0) + (obj.sgst_amount or 0.0) + (obj.igst_amount or 0.0)

        return '-'
    get_net_amount.short_description = 'Net Amount (₹)'


class AlliancePartnerOrderAdmin(CustomAdminTitle):
    ''' Distributor Orders options '''
    inlines = [AlliancePartnerDetailInline, ]
    model = AlliancePartnerOrder
    form = AllianceOrderAdminForm
    list_per_page = ADMIN_PAGE_SIZE
    fieldsets = (
        (None, {
            'fields': ('distributor', 'shipping_address'),
            'classes': ('cols-2',)
        }),
        (None, {
            'fields': ('order_status', 'payment_status',
                       'cancel_order', 'cancel_reason'),
            'classes': ('cols-2',)
        }),
        (None, {
            'fields': ('invoice_number', 'amount', 'total_amount', 'discount_amount',
                       'get_claim_discount', 'get_total_amount', 'invoice_number_alliance', 'get_gst_code'),
            'classes': ('cols-2',)
        }),
    )
    list_display = ('get_order_id', 'distributor', 'created_date', 'dispatched_date',
                    'order_status', 'payment_status', 'order_actions', 'moc')
    search_fields = ['id', 'alliance_code', 'distributor__username',
                     'distributor__name', 'distributor__email', 'invoice_number', 'invoice_number_alliance']
    list_filter = (('created', DateRangeFilter),
                   OrderStatusFilter, DistributorFilter, ('modified', custom_titled_filter(
                       'Date')),
                   )
    _list_filter = (('created', DateRangeFilter), OrderStatusFilter, DistributorFilter, AllianceFilter,
                    ('modified', custom_titled_filter('Date')),
                    )
    readonly_fields = ('get_claim_discount',
                       'get_total_amount', 'get_gst_code')

    change_list_template = "admin/orders/change_list.html"

    actions = ['export_order_list']

      



    def export_order_list(self, request, queryset):
        data_headers = ['ORDER ID', 'CREATED ON', 'DISPATCHED ON', 'REDISTRIBUTION STOCKIST', 'PIL CODE', 'HUL CODE', 'SHIPPING ADDRESS', 'ORDER STATUS', 'PAYMENT STATUS',
                        'ORDER AMOUNT', 'TOTAL AMOUNT', 'INVOICE NUMBER', 'ALLIANCE_INVOICE_NUMBER', 'MOC',
                        'PRODUCT CODE', 'PRODUCT NAME', 'ORDER CASES', 'ORDERED UNITS', 'DISPATCH CASES', 'DISPATCH UNITS', 'INVOICE PRICE',
                        'CGST', 'SGST', 'IGST', 'PRICE', 'NET AMOUNT', 'ITEM STATUS']
        data = tablib.Dataset(headers=data_headers, title='Orders')

        for order in queryset:
            order_details = order.alliancepartnerorderdetail_set.all()
            created_date = str(order.created.date())
            dispatch_date = str(order.dispatched_on.date()
                                ) if order.dispatched_on else ' '
            for order_detail in order_details:
                row = (order.pk, created_date, dispatch_date, str(order.distributor), str(order.distributor.regionaldistributor.code),
                       str(order.distributor.regionaldistributor.hul_code),
                       str(order.shipping_address), order.get_order_status_display(),
                       order.get_payment_status_display(), order.amount, order.total_amount,
                       order.invoice_number, order.invoice_number_alliance, order.get_moc_name(
                ), order_detail.product.basepack_code, order_detail.product.basepack_name,
                    order_detail.get_cases(), order_detail.get_units(), order_detail.get_dispatch_cases(),
                    order_detail.get_dispatch_units(), order_detail.unitprice,
                    order_detail.cgst_amount, order_detail.sgst_amount, order_detail.igst_amount,
                    order_detail.price,
                    (order_detail.price or 0.0) - order_detail.discount_amount + (order_detail.cgst_amount or 0.0) +
                    (order_detail.sgst_amount or 0.0) +
                    (order_detail.igst_amount or 0.0),
                    order_detail.get_item_status_display())
                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="PrimaryOrder.xls"'
        response.write(data.export('xls'))
        return response
    export_order_list.short_description = 'Export Orders'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Orders'
        return super(AlliancePartnerOrderAdmin, self).changelist_view(*args, **kwargs)

    class Media:
        '''
        adding custom media to admin
        '''
        js = ('admin/orders/js/order_management.js',
              'admin/orders/js/orders.js?v=1')
        css = {
            'all': ('admin/orders/css/order_management.css',)
        }

    def get_order_id(self, obj):
        '''
        Return Order Id
        '''
        return obj.alliance_code + str(obj.pk).zfill(6)
    get_order_id.short_description = 'Order ID'

    @classmethod
    def order_actions(cls, obj):
        '''
        Return Order Action View Invoice
        '''
        html = 'N/A'

        if obj.order_status in [OrderStatus.INTRANSIT, OrderStatus.RECEIVED]:
            html = format_html('<a target="_blank" href="{}"> View Invoice</a>',
                               reverse('alliance-order-invoice', args=[obj.pk]))
        return html

    def get_queryset(self, request):
        queryset = super(AlliancePartnerOrderAdmin, self).get_queryset(request).\
            select_related('distributor')

        if not request.user.is_superuser and hasattr(request.user, 'alliancepartner'):
            queryset = queryset.filter(alliance=request.user)

        if not request.user.is_superuser and hasattr(request.user, 'regionaldistributor'):
            queryset = queryset.filter(distributor=request.user)

        return queryset

    # def get_search_results(self, request, queryset, search_term):
    #     queryset, use_distinct = super(AlliancePartnerOrderAdmin, self).get_search_results(request, queryset, search_term)
    #     try:
    #         search_term_as_int = int(search_term)
    #     except ValueError:
    #         pass
    #     else:
    #         queryset |= self.model.objects.annotate(
    #             idzip=F('pk')
    #         ).values(
    #             'idzip'
    #         ).annotate(
    #             idz=LPad(Cast('idzip', MCharField()), 6, fill_text=V('0'))
    #         ).values(
    #             'idzip', 'idz'
    #         ).annotate(
    #             order=Concat('alliance_code', 'idz', output_field=CharField())
    #         ).filter(order=str(search_term_as_int))
    #     return queryset, use_distinct

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return False

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(AlliancePartnerOrderAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def get_claim_discount(self, obj):
        '''
        get total discount amount for this order
        '''
        amount = 0
        if hasattr(obj, 'alliancepartnershaktidiscount_set'):
            shakti_discount = obj.alliancepartnershaktidiscount_set.aggregate(
                shakti_discount=Sum('discount_amount'))
            amount += shakti_discount['shakti_discount'] or 0

        if hasattr(obj, 'alliancepartnerdiscountdetail_set'):
            discount = obj.alliancepartnerdiscountdetail_set.aggregate(
                discount=Sum('discount_amount'))
            amount += discount['discount'] or 0

        return amount
    get_claim_discount.short_description = 'Claim (₹)'

    def get_gst_code(self, obj):
        return obj.distributor.regionaldistributor.gst_code
    get_gst_code.short_description = 'Gst Code'

    def get_total_amount(self, obj):
        '''
        get total discount amount for this order
        '''
        amount = self.get_claim_discount(obj)
        return obj.total_amount - obj.discount_amount - amount
    get_total_amount.short_description = 'Grand Total (₹)'

    def created_date(self, obj):
        '''
        created date formating
        '''
        return obj.created.strftime("%d %b %Y")
    created_date.short_description = 'Created'

    def dispatched_date(self, obj):
        '''
        dispatched date formating
        '''
        return obj.dispatched_on.strftime("%d %b %Y") if obj.dispatched_on else None
    dispatched_date.short_description = 'Dispacthed'

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj:
            for field in self.opts.local_fields:
                if field.name not in readony_list and field.name not in ['order_status',
                                                                         'payment_status',
                                                                         'cancel_order',
                                                                         'cancel_reason']:
                    readony_list.append(field.name)
            if obj.order_status == OrderStatus.CANCELLED:
                readony_list.extend(['payment_status',
                                     'cancel_order', 'cancel_reason'])
            if request.user.is_superuser or hasattr(request.user, 'alliancepartner'):
                readony_list.extend(['order_status', 'payment_status',
                                     'cancel_order', 'cancel_reason'])
        return readony_list

    def get_list_filter(self, request):
        ''' modify filters list accroding to logged in user '''
        filter_list = self._list_filter
        if not request.user.is_superuser:
            filter_list = self.list_filter
        return filter_list

    def response_change(self, request, obj):
        ''' redirecting after saving order '''
        if obj.order_status == OrderStatus.DISPATCHED:
            return HttpResponseRedirect(reverse('dispatch_alliance_order',
                                                kwargs={'order_id': obj.id}))
        else:
            return super(AlliancePartnerOrderAdmin, self).response_change(request, obj)

    def save_model(self, request, obj, form, change):
        ''' override save model for redirecting to dispatch page '''

        if change and obj.order_status != OrderStatus.DISPATCHED:
            super(AlliancePartnerOrderAdmin, self).save_model(
                request, obj, form, change)

    def save_formset(self, request, form, formsets, change):
        ''' avoid save related if status is dispatch '''

        if change and form.instance.order_status != OrderStatus.DISPATCHED:
            super(AlliancePartnerOrderAdmin, self).save_formset(
                request, form, formsets, change)
        else:
            instances = formsets.save(commit=False)
            for instance in instances:
                old_value = AlliancePartnerOrderDetail.objects.values(
                    'item_status').get(pk=instance.pk)
                instance.item_status = old_value['item_status']
                instance.save()


class StateFilter(admin.SimpleListFilter):

    title = 'State'
    parameter_name = 'state'

    def lookups(self, request, model_admin):
        queryset = State.objects.filter(
            state__do_shipping__isnull=False).distinct()
        return queryset.values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(distributor__do_distributor_related__shipping_address__state=self.value())
        return queryset


class DistributerStockAdmin(CustomAdminTitle):
    ''' Distributor Orders options '''
    model = DistributorStock
    fields = ['product', 'distributor',
              'opening_stock', 'closing_stock', 'amount', ]
    list_display = ('product', 'distributor',
                    'get_cases', 'get_units', 'amount', 'created', 'get_basepack_code', 'get_distributor_code')
    list_select_related = ['distributor', 'product__brand__user', ]
    list_display_links = ()
    list_filter = ['product__brand', ('created', DateRangeFilter)]
    readonly_fields = ['product', 'distributor',
                       'opening_stock', 'closing_stock', 'amount']

    search_fields = ['distributor__name', 'product__basepack_name']

    change_list_template = 'admin/orders/distributorstock_change_list.html'

    actions = ['export_stock']

    def export_stock(self, request, queryset):
        data_headers = ['PRODUCT', 'DISTRIBUTOR', 'CASES', 'UNITS',
                        'AMOUNT', 'DATE', 'BASEPACK CODE', 'DISTRIBUTOR CODE']
        data = tablib.Dataset(headers=data_headers, title='DistributorStock')

        for stock in queryset:
            row = (
                stock.product.basepack_name, stock.distributor.name,
                divmod(stock.closing_stock,
                       stock.product.cld_configurations)[0],
                divmod(stock.closing_stock,
                       stock.product.cld_configurations)[1],
                stock.amount, str(stock.created.astimezone(timezone(
                    'Asia/Kolkata')).date()), stock.get_basepack_code(), stock.get_distributor_code()
            )
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="DistributorStock.xls"'
        response.write(data.export('xls'))
        return response
    export_stock.short_description = 'Export Stock'

    def changelist_view(self, request, extra_context=None):
        if not request.user.is_superuser:
            self.list_display_links = None
        else:
            self.list_display_links = ()
        total = self.get_queryset(request).aggregate(
            total=Sum('amount'))['total']
        my_context = {
            'total': total,
            'export_title': 'Export Stock'
        }
        return super(DistributerStockAdmin, self).changelist_view(request,
                                                                  extra_context=my_context)

    def get_queryset(self, request):
        queryset = super(DistributerStockAdmin, self).get_queryset(request
                                                                   ).select_related('distributor', 'product', 'product__brand__user', ).distinct()

        if hasattr(request.user, 'regionaldistributor'):
            queryset = queryset.filter(
                distributor=request.user).order_by('-created')
        return queryset

    def get_units(self, obj=None):
        ''' convert ordered quantity to units '''
        units = divmod(obj.closing_stock, obj.product.cld_configurations)
        return units[1]
    get_units.short_description = 'Closing Units'

    def get_cases(self, obj=None):
        ''' convert ordered quantity to cases '''
        units = divmod(obj.closing_stock, obj.product.cld_configurations)
        return units[0]
    get_cases.short_description = 'Closing Cases'

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return False

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(DistributerStockAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj and (obj.created.astimezone(timezone('Asia/Kolkata')).date() == dt.now().date()):
            readony_list.remove('closing_stock')
        return readony_list

    def save_model(self, request, obj, form, change):
        ''' override save model for calculating stock price '''
        obj.amount = obj.product.tur * obj.closing_stock
        super(DistributerStockAdmin, self).save_model(
            request, obj, form, change)


class ReviewPrimaryOrderDetailInline(admin.TabularInline):
    model = ReviewPrimaryOrderDetail
    extra = 0
    fields = ('product', 'get_basepack_code', 'get_cld', 'get_norm',
              'get_stock_inhand', 'get_stock_inhand_price', 'get_stock_intransit',
              'get_stock_intransit_price', 'order_generated',
              'unitprice', 'price', 'cgst_amount', 'sgst_amount', 'igst_amount',
              'get_net_amount')
    readonly_fields = ['product', 'get_basepack_code', 'get_cld',
                       'get_norm', 'get_stock_inhand', 'get_stock_inhand_price',
                       'get_stock_intransit_price', 'get_stock_intransit',
                       'unitprice', 'price', 'cgst_amount', 'sgst_amount', 'igst_amount', 'get_net_amount']

    def get_queryset(self, request):
        queryset = super(ReviewPrimaryOrderDetailInline, self).get_queryset(request).\
            select_related('product')
        return queryset

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        return False

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj and (obj.is_placed or obj.is_discarded):
            readony_list.extend(['order_generated'])
        return readony_list

    def get_net_amount(self, obj=None):
        '''
        return price + taxes
        '''
        if obj:
            return (obj.price or 0.0) + (obj.cgst_amount or 0.0) + (obj.sgst_amount or 0.0) + (obj.igst_amount or 0.0)

        return '-'
    get_net_amount.short_description = 'Net Amount (₹)'

    class Media:
        '''
        adding custom pop up to review primary orders
        '''
        js = ('admin/orders/js/order_disclaimer.js',)


class ReviewPrimaryOrderAdmin(CustomAdminTitle):
    inlines = [ReviewPrimaryOrderDetailInline, ]
    model = ReviewPrimaryOrder
    list_display = ('id', 'distributor', 'shipping_address',
                    'tax', 'total_amount', 'created', 'is_placed', 'is_discarded')
    search_fields = ['id',  'distributor__username',
                     'distributor__name', 'distributor__email']
    fieldsets = (
        (None, {
            'fields': ('distributor', 'shipping_address', 'get_distributor_min_order',
                       'tax', 'total_amount'),
        }),
    )
    readonly_fields = ('distributor', 'shipping_address',
                       'tax', 'get_distributor_min_order', 'total_amount')

    change_list_template = "admin/orders/change_list.html"

    actions = ['export_order_list']

    def export_order_list(self, request, queryset):
        data_headers = ['ORDER ID', 'REDISTRIBUTION STOCKIST', 'PIL CODE', 'SHIPPING ADDRESS', 'MINIMUM ORDER', 'TAX', 'TOTAL AMOUNT',
                        'PRODUCT', 'PRODUCT CODE', 'BASEPACK CODE', 'CLD CONFIGURATION', 'NORM', 'STOCK IN HAND', 'STOCK IN HAND VALUE',
                        'STOCK IN TRANSIT', 'STOCK IN TRANSIT VALUE', 'ORDER GENERATED (IN CASES)', 'INVOICE PRICE', 'CGST AMOUNT',
                        'SGST AMOUNT', 'IGST AMOUNT', 'PRICE']
        data = tablib.Dataset(headers=data_headers, title='Review Orders')

        for order in queryset:
            order_details = order.reviewprimaryorderdetail_set.all()
            for order_detail in order_details:
                row = (order.pk, str(order.distributor), str(order.distributor.regionaldistributor.code), str(order.shipping_address), str(order.amount),
                       order.tax, order.total_amount, order_detail.product_id, str(
                           order_detail.product),
                       order_detail.product.basepack_code, order_detail.product.cld_configurations,
                       order_detail.get_norm(),
                       order_detail.get_stock_inhand(),  order_detail.get_stock_inhand_price(),
                       order_detail.get_stock_intransit(), order_detail.get_stock_intransit_price(),
                       order_detail.order_generated, order_detail.unitprice,
                       order_detail.cgst_amount, order_detail.sgst_amount,
                       order_detail.igst_amount, order_detail.price)
                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ReviewPrimaryOrder.xls"'
        response.write(data.export('xls'))
        return response
    export_order_list.short_description = 'Export Orders'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Orders'
        return super(ReviewPrimaryOrderAdmin, self).changelist_view(*args, **kwargs)

    def get_distributor_min_order(self, obj=None):
        min_order = ''
        if obj:
            min_order = obj.distributor.regionaldistributor.min_order

        return min_order
    get_distributor_min_order.short_description = 'Minimum Order (₹)'

    def get_list_display(self, request):
        default_list_display = super(
            ReviewPrimaryOrderAdmin, self).get_list_display(request)
        if not request.user.is_superuser:
            lst = list(default_list_display)
            lst.remove('distributor')
            return tuple(lst)
        return default_list_display

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            remove_from_fieldsets(self.fieldsets, ('distributor',))

        return super(ReviewPrimaryOrderAdmin, self).get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super(ReviewPrimaryOrderAdmin, self).get_queryset(request)
        qs = qs.select_related(
            'distributor', 'distributor__regionaldistributor',
            'shipping_address', 'shipping_address__country', 'shipping_address__state')
        if request.user.is_superuser:
            return qs
        return qs.filter(distributor=request.user, is_placed=False)

    @classmethod
    def has_add_permission(cls, request):
        return False

    def get_actions(self, request):
        actions = super(ReviewPrimaryOrderAdmin, self).get_actions(request)

        if 'delete_selected' in actions:
            del actions['delete_selected']

        return actions

    def save_formset(self, request, form, formset, change):
        formset.save()
        form_obj = form.instance
        total_amount = 0
        total_tax = 0

        for f in formset.forms:
            obj = f.instance
            taxable_amount = obj.price
            if f.has_changed():
                taxable_amount = obj.unitprice * \
                    obj.order_generated * obj.product.cld_configurations

                obj.cgst_amount = taxable_amount * obj.product.cgst / 100
                obj.sgst_amount = taxable_amount * obj.product.sgst / 100
                obj.igst_amount = taxable_amount * obj.product.igst / 100
                obj.price = taxable_amount
                obj.save()

            total_amount += taxable_amount + \
                (obj.cgst_amount + obj.igst_amount + obj.sgst_amount)
            total_tax += (obj.cgst_amount + obj.igst_amount + obj.sgst_amount)

        if total_amount < obj.review_primary_order.distributor.regionaldistributor.min_order:
            messages.warning(request,
                             "Please increase order value for successfull generation of order.")

        form_obj.total_amount = total_amount
        form_obj.tax = total_tax
        form_obj.save()


# secondary orders
admin.site.register(DistributorOrder, DistributorOrderAdmin)
# primary orders
admin.site.register(AlliancePartnerOrder, AlliancePartnerOrderAdmin)
admin.site.register(DistributorStock, DistributerStockAdmin)
admin.site.register(ReviewPrimaryOrder, ReviewPrimaryOrderAdmin)
