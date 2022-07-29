# -*- coding: utf-8 -*-
import tablib
from django.http import HttpResponse
from django.contrib import admin
from django.db.models import Sum
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.admin.views.main import ChangeList
from django_admin_listfilter_dropdown.filters import DropdownFilter, RelatedDropdownFilter

from hul.utility import CustomAdminTitle
from hul.choices import ClaimStatus

from orders.filters import AllianceFilter, DistributorFilter
from claim.models import Claim
from claim.sql import ClaimDetail
from orders.models import DistributorOrderDetail, AlliancePartnerShaktiDiscount
from orders.filters import RangeTextInputFilter


class DateFilter(RangeTextInputFilter):
    title = 'date range'
    parameter_name = 'date range'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                created__gte=self.value()[0], created__lte=self.value()[1])
        return queryset


class ClaimChangeList(ChangeList):
    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return 'detail/%d/' % (pk)


class ClaimAdmin(CustomAdminTitle):
    model = Claim
    list_display = ['invoice_number',
                    'get_claim_date', 'distributor', 'alliance',
                    'get_discount', 'claim_status']
    list_display_links = ('invoice_number', )
    list_select_related = ['distributor',
                           'alliance']
    _list_filter = [AllianceFilter, DistributorFilter, DateFilter]
    distributor_list_filter = [DistributorFilter, DateFilter]
    fields = ('invoice_number',
              'get_claim_date', 'distributor', 'alliance',
              'get_discount')

    readonly_fields = ['invoice_number',
                       'get_claim_date', 'distributor', 'alliance',
                       'get_discount']

    change_list_template = "admin/claim/change_list.html"
    actions = ['process_claim', 'export_claim_list']

    def export_claim_list(self, request, queryset):
        data_headers = ['CLAIM ID:', 'CLAIM SETTLEMENT MONTH', 'REDISTRIBUTION STOCKIST', 'ALLIANCE', 'ORDERED AMOUNT',
                        'DISCOUNTED AMOUNT', 'STATUS', 'PRODUCT NAME', 'BASEPACK CODE', 'SHAKTI ENTREPRENEUR',
                        'SHAKTI ENTREPRENEUR CODE', 'OFFER(S) APPLIED', 'AMOUNT CLAIMED']
        data = tablib.Dataset(headers=data_headers, title='Claims')

        for claim in queryset:
            claim_data = ClaimDetail.get_claim_detail(claim.id)
            bonus_data = AlliancePartnerShaktiDiscount.objects.filter(
                alliance_partner_order=claim.id
            ).select_related('shakti_enterpreneur')
            claim_id = 'CLM-{0}'.format(claim_data[0]['invoice_number'])
            month = '{0}, {1}'.format(
                claim_data[0]['settlement_month'], claim_data[0]['settlement_year'])
            distributor = claim_data[0]['distributor']
            alliance = claim_data[0]['alliance']

            ordered_amount = sum(item['ordered_amount'] for item in claim_data)

            product_sum = sum(item['discount_amount'] for item in claim_data)
            bonus_sum = sum(item.discount_amount for item in bonus_data)
            discount = product_sum + bonus_sum or 0

            label = ClaimStatus.LABEL[claim_data[0]['claim_status']]

            for product in claim_data:
                row = [claim_id, month, distributor, alliance, ordered_amount, discount, label,
                       product['basepack_name'], product['basepack_code'], product['shakti_name'], product['code'],
                       product['offer'],
                       product['discount_amount']]

                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="Claims.xls"'
        response.write(data.export('xls'))
        return response
    export_claim_list.short_description = 'Export Claims'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Claims'
        return super(ClaimAdmin, self).changelist_view(*args, **kwargs)

    def get_changelist(self, request, **kwargs):
        return ClaimChangeList

    def get_urls(self):
        urls = super(ClaimAdmin, self).get_urls()
        custom_urls = [
            url(r'^(?i)detail/(?P<order_id>[0-9]+)/$',
                self.admin_site.admin_view(self.claim_detail),
                name='claim_detail'),
        ]
        return custom_urls + urls

    def claim_detail(self, request, order_id=None):
        ''' get Claim details for a invoice '''

        claim_data = ClaimDetail.get_claim_detail(order_id)
        bonus_data = AlliancePartnerShaktiDiscount.objects.filter(
            alliance_partner_order=order_id
        ).select_related('shakti_enterpreneur')

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context = dict(
            self.admin_site.each_context(request),
            title='Claim Details',
            is_popup=False,
            to_field='',
            refaral_url='/admin/claim/claim',
            refaral_name='Claim',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            detail=claim_data,
            bonus=bonus_data,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/claim/detail.html',
            context,
        )

    def get_claim_date(self, obj):
        return obj.created
    get_claim_date.short_description = 'Claim Date'

    def get_discount(self, obj):
        '''
        get sum of shakti bonus and offers discount
        '''
        discount_set = obj.alliancepartnerdiscountdetail_set.aggregate(
            sum=Sum('discount_amount'))

        bonus_set = obj.alliancepartnershaktidiscount_set.aggregate(
            sum=Sum('discount_amount'))

        return (discount_set['sum'] or 0.0) + (bonus_set['sum'] or 0.0)
    get_discount.short_description = 'Discount Amount (₹)'

    def process_claim(self, request, queryset):
        '''
        Custom function to Process claims action
        '''
        queryset.update(claim_status=ClaimStatus.PROCESSED)
        self.message_user(
            request, "Selected claim(s) processed successfully.")
    process_claim.short_description = "Process selected claim(s)"

    def get_actions(self, request):
        actions = super(ClaimAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def get_list_display(self, request):

        default_list_display = super(
            ClaimAdmin, self).get_list_display(request)

        if hasattr(request.user, 'regionaldistributor'):
            lst = list(default_list_display)
            lst.remove('distributor')
            return tuple(lst)

        if hasattr(request.user, 'alliancepartner'):
            lst = list(default_list_display)
            lst.remove('alliance')
            return tuple(lst)

        return default_list_display

    def get_list_filter(self, request):
        ''' modify filters list accroding to logged in user '''
        filter_list = self._list_filter
        if hasattr(request.user, 'alliancepartner'):
            filter_list = self.distributor_list_filter
        return filter_list

    def get_queryset(self, request):
        queryset = super(ClaimAdmin, self).get_queryset(request)

        if hasattr(request.user, 'regionaldistributor'):
            queryset = queryset.filter(distributor=request.user)

        if hasattr(request.user, 'alliancepartner'):
            queryset = queryset.filter(alliance=request.user)
        return queryset

    def has_add_permission(self, obj):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# admin.site.register(Claim, ClaimAdmin)
