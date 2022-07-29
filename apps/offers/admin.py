''' offers/admin.py '''
import tablib
from django.http import HttpResponse
from django.contrib import admin, messages
from django.core.urlresolvers import reverse_lazy
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import format_html
from django.conf.urls import url
from django.template.response import TemplateResponse
from django.http.response import HttpResponseRedirect
from django.db import IntegrityError

from tablib import Dataset

from hul.utility import CustomAdminTitle

from app.models import RegionalDistributor
from offers.models import (ShaktiBonus, ShaktiBonusLines,
                           ShaktiBonusAll, ShaktiBonusAllLines,
                           ShaktiPromotions, ShaktiPromotionLines,
                           ShaktiOffers, ShaktiOffersLines,
                           TradeOffers, TradeOffersLines,
                           DiscountToShakti)
from app.forms import UserImportForm
from offers.import_offers import ImportOffers, ImportProcess, ImportPromotions
from offers.conf import SHAKTI_BONUS_FIELDS, TRADE_OFFERS_FIELDS, SHAKTI_PROMOTION_FIELDS


def generate_delete_html(self, obj):
    url = 'admin:{app_label}_{model_name}_delete'.format(
        app_label=self.opts.app_label, model_name=self.opts.model_name)
    html = format_html('<a href="{}"> Delete </a>',
                       reverse_lazy(url, args=[obj.pk]))
    return html


class BonusLinesAdmin(admin.TabularInline):
    model = ShaktiBonusLines
    min_num = 1
    max_num = 3
    extra = 0
    fields = ('target_amount', 'discount_type', 'discount')


class BonusAdmin(CustomAdminTitle):
    inlines = [BonusLinesAdmin]

    raw_id_fields = ('shakti_enterpreneur',)
    list_display = ('id', 'shakti_enterpreneur',
                    'end', 'get_delete_url')

    search_fields = ['shakti_enterpreneur__user__name',
                     'shaktibonuslines__target_amount']

    model = ShaktiBonus
    change_list_template = "admin/offers/change_list.html"
    actions = ['export_offers_list']

    fieldsets = (
        (None, {
            'fields': ('shakti_enterpreneur', 'start',
                       'end'),

        }),
    )

    def export_offers_list(self, request, queryset):
        data_headers = ['Shakti Code', 'Start Date (mm/dd/yyyy)', 'Expires on (mm/dd/yyyy)', 'Target Amount 1', 'Discount 1',
                        'Target Amount 2', 'Discount 2', 'Target Amount 3', 'Discount 3']
        data = tablib.Dataset(headers=data_headers, title='Bonus')
        empty_line = ['', '']
        for bonus in queryset:
            row = [bonus.shakti_enterpreneur.code, bonus.start.strftime(
                '%m/%d/%Y'), bonus.end.strftime('%m/%d/%Y')]
            bonus_lines = bonus.shaktibonuslines_set.all()
            line_count = bonus_lines.count()
            for bonus_line in bonus_lines:
                row2 = [bonus_line.target_amount, bonus_line.discount]
                row.extend(row2)
            while line_count < 3:
                row.extend(empty_line)
                line_count += 1
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ShaktiBonus.xls"'
        response.write(data.export('xls'))
        return response
    export_offers_list.short_description = 'Export Bonus'

    def changelist_view(self, *args, **kwargs):
        '''
        adding extra context for changelist of Shakti Bonus
        '''
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import Shakti Bonus'
        kwargs['extra_context']['export_title'] = 'Export Shakti Bonus'
        return super(BonusAdmin, self).changelist_view(*args, **kwargs)

    def get_urls(self):
        urls = super(BonusAdmin, self).get_urls()
        custom_urls = [
            url(r'^(?i)import/$',
                self.admin_site.admin_view(self.import_bonus),
                name='import_shakti'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
        ]
        return custom_urls + urls

    def import_bonus(self, request):
        ''' Import Shakti Users '''
        form = UserImportForm()
        # import_process = ImportProcess()
        error_list = []
        if request.POST:
            dataset = Dataset()
            form = UserImportForm(request.POST, request.FILES)
            shakti_bonus = request.FILES['import_file']
            try:
                imported_data = dataset.load(shakti_bonus.read())
                import_obj = ImportOffers()
                error_list = import_obj.process_file(request, imported_data)
            except StandardError as error:
                error_list = [error.message]
            if not error_list:
                return HttpResponseRedirect(reverse_lazy("admin:offers_shaktipromotions_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Shakti Bonus',
            is_popup=False,
            to_field='',
            error_list=error_list,
            refaral_url='/admin/offers/shaktibonus',
            refaral_name='Shakti Bonus',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            action_form=form,
            form=form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/offers/import.html',
            context,
        )

    def sample_export_csv(self, request):
        ''' Sample CSV file '''
        return ImportOffers().sample_export_csv(SHAKTI_BONUS_FIELDS,
                                                'shakti_bonus_sample.csv')

    def get_delete_url(self, obj):
        html = generate_delete_html(self, obj)
        return html
    get_delete_url.short_description = 'Action'


class BonusAllLinesAdmin(admin.TabularInline):
    model = ShaktiBonusAllLines
    min_num = 1
    max_num = 3
    extra = 0
    fields = ('target_amount', 'discount_type', 'discount')


class BonusAllAdmin(CustomAdminTitle):
    inlines = [BonusAllLinesAdmin]
    list_display = ('id',
                    'end', 'get_delete_url')

    search_fields = [
        'shaktibonuslines__target_amount']

    model = ShaktiBonusAll
    change_list_template = "admin/offers/change_list.html"
    actions = ['export_offers_list']
    fieldsets = (
        (None, {
            'fields': ('start', 'end'),
        }),
    )

    def get_delete_url(self, obj):
        html = generate_delete_html(self, obj)
        return html
    get_delete_url.short_description = 'Action'

    def changelist_view(self, *args, **kwargs):
        '''
        adding extra context for changelist of Shakti Bonus
        '''
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Bonus to All'
        return super(BonusAllAdmin, self).changelist_view(*args, **kwargs)

    def export_offers_list(self, request, queryset):
        data_headers = ['Start Date (mm/dd/yyyy)', 'Expires on (mm/dd/yyyy)', 'Target Amount 1', 'Discount 1',
                        'Target Amount 2', 'Discount 2', 'Target Amount 3', 'Discount 3']
        data = tablib.Dataset(headers=data_headers, title='Bonus')
        empty_line = ['', '']
        for bonus in queryset:
            row = [bonus.start.strftime(
                '%m/%d/%Y'), bonus.end.strftime('%m/%d/%Y')]
            bonus_lines = bonus.shaktibonuslines_set.all()
            line_count = bonus_lines.count()
            for bonus_line in bonus_lines:
                row2 = [bonus_line.target_amount, bonus_line.discount]
                row.extend(row2)
            while line_count < 3:
                row.extend(empty_line)
                line_count += 1
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ShaktiBonus.xls"'
        response.write(data.export('xls'))
        return response


class ShaktiPromotionLinesAdmin(admin.TabularInline):
    model = ShaktiPromotionLines
    min_num = 1
    extra = 0
    fields = ('buy_product', 'buy_quantity', 'discount')


class ShaktiPromotionsAdmin(CustomAdminTitle):
    model = ShaktiPromotions
    inlines = [ShaktiPromotionLinesAdmin]
    raw_id_fields = ('shakti_enterpreneur',)
    list_display = ('id', 'name', 'shakti_enterpreneur',
                    'end', 'get_delete_url')

    search_fields = ['shakti_enterpreneur__user__name',
                     'name', 'promotionlines__buy_product__basepack_name']

    fieldsets = (
        (None, {
            'fields': ('name', 'shakti_enterpreneur', 'start',
                       'end'),

        }),
    )
    change_list_template = "admin/offers/change_list.html"
    actions = ['export_offers_list']

    def export_offers_list(self, request, queryset):
        data_headers = ['Name', 'Shakti Code', 'Start Date (mm/dd/yyyy)', 'Expires on (mm/dd/yyyy)', 'Buy Product',
                        'Buy Quantity', 'Discount', ]
        data = tablib.Dataset(headers=data_headers, title='Promotions')

        for promotion in queryset:
            shakti = promotion.shakti_enterpreneur.code
            start = promotion.start.strftime('%m/%d/%Y')
            end = promotion.end.strftime('%m/%d/%Y')

            offer_lines = promotion.promotionlines_set.all()

            for offer_line in offer_lines:
                row = [promotion.name, shakti, start, end, str(offer_line.buy_product),
                       offer_line.buy_quantity, offer_line.discount]

                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ShaktiPromotions.xls"'
        response.write(data.export('xls'))
        return response
    export_offers_list.short_description = 'Export Promotions'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import Shakti Promotions'
        kwargs['extra_context']['export_title'] = 'Export Shakti Promotions'
        return super(ShaktiPromotionsAdmin, self).changelist_view(*args, **kwargs)

    def get_urls(self):
        urls = super(ShaktiPromotionsAdmin, self).get_urls()
        custom_urls = [
            url(r'^(?i)import/$',
                self.admin_site.admin_view(self.import_promotion),
                name='import_shakti'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
        ]
        return custom_urls + urls

    def get_delete_url(self, obj):
        html = generate_delete_html(self, obj)
        return html
    get_delete_url.short_description = 'Action'

    def import_promotion(self, request):
        ''' Import Shakti Users '''
        form = UserImportForm()
        # import_process = ImportProcess()
        error_list = []
        if request.POST:
            dataset = Dataset()
            form = UserImportForm(request.POST, request.FILES)
            shakti_bonus = request.FILES['import_file']
            try:
                imported_data = dataset.load(shakti_bonus.read())
                import_obj = ImportPromotions()
                error_list = import_obj.process_file(request, imported_data)
            except StandardError as error:
                error_list = [error.message]
            if not error_list:
                return HttpResponseRedirect(reverse_lazy("admin:offers_shaktipromotions_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Shakti Promotions',
            is_popup=False,
            to_field='',
            error_list=error_list,
            refaral_url='/admin/offers/shaktipromotions',
            refaral_name='Shakti Promotions',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            action_form=form,
            form=form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/offers/import.html',
            context,
        )

    def sample_export_csv(self, request):
        ''' Sample CSV file '''
        return ImportOffers().sample_export_csv(SHAKTI_PROMOTION_FIELDS,
                                                'shakti_promotions_sample.csv')


class ShaktiOffersLinesAdmin(admin.TabularInline):
    model = ShaktiOffersLines
    min_num = 1
    extra = 0
    fields = ('buy_product', 'buy_quantity', 'free_product', 'free_quantity')


class ShaktiOffersAdmin(CustomAdminTitle):
    model = ShaktiOffers
    inlines = [ShaktiOffersLinesAdmin]
    raw_id_fields = ('shakti_enterpreneur',)
    list_display = ('id', 'name', 'shakti_enterpreneur',
                    'end', 'get_delete_url')

    search_fields = ['shakti_enterpreneur__user__name',
                     'name', 'promotionlines__buy_product__basepack_name']

    fieldsets = (
        (None, {
            'fields': ('name', 'shakti_enterpreneur', 'start',
                       'end'),

        }),
    )

    change_list_template = "admin/offers/change_list.html"
    actions = ['export_offers_list']

    def export_offers_list(self, request, queryset):
        data_headers = ['Name', 'Shakti Code', 'Start Date (mm/dd/yyyy)', 'Expires on (mm/dd/yyyy)', 'Buy Product',
                        'Buy Quantity', 'Free Product', 'Free Quantity', ]
        data = tablib.Dataset(headers=data_headers, title='offers')

        for offer in queryset:
            shakti = offer.shakti_enterpreneur.code
            start = offer.start.strftime('%m/%d/%Y')
            end = offer.end.strftime('%m/%d/%Y')
            offer_lines = offer.promotionlines_set.all()

            for offer_line in offer_lines:
                row = [offer.name, shakti, start, end, str(offer_line.buy_product),
                       offer_line.buy_quantity, str(offer_line.free_product), offer_line.free_quantity]

                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ShaktiOffers.xls"'
        response.write(data.export('xls'))
        return response
    export_offers_list.short_description = 'Export Offers'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Shakti Offers'
        return super(ShaktiOffersAdmin, self).changelist_view(*args, **kwargs)

    def get_delete_url(self, obj):
        html = generate_delete_html(self, obj)
        return html
    get_delete_url.short_description = 'Action'


class TradeOffersLinesAdmin(admin.TabularInline):
    model = TradeOffersLines
    min_num = 1
    extra = 0
    fields = ('buy_product', 'buy_quantity', 'discount')


class TradeOffersAdmin(CustomAdminTitle):
    model = TradeOffers
    inlines = [TradeOffersLinesAdmin]
    list_display = ('id', 'name', 'end', 'get_delete_url')
    search_fields = ['shakti_enterpreneur__user__name',
                     'name', 'promotionlines__buy_product__basepack_name']

    fieldsets = (
        (None, {
            'fields': ('name', 'start',
                       'end'),

        }),
    )
    change_list_template = "admin/offers/change_list.html"
    actions = ['export_offers_list']

    def export_offers_list(self, request, queryset):
        data_headers = ['Name', 'Start Date (mm/dd/yyyy)', 'Expires on (mm/dd/yyyy)', 'Buy Product',
                        'Buy Quantity', 'Discount', ]
        data = tablib.Dataset(headers=data_headers, title='Trade Offers')

        for trade in queryset:
            start = trade.start.strftime('%m/%d/%Y')
            end = trade.end.strftime('%m/%d/%Y')

            offer_lines = trade.promotionlines_set.all()

            for offer_line in offer_lines:
                row = [trade.name, start, end, str(offer_line.buy_product),
                       offer_line.buy_quantity, offer_line.discount]

                data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="Trade Offers.xls"'
        response.write(data.export('xls'))
        return response
    export_offers_list.short_description = 'Export Trade Offers'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Trade Offers'
        kwargs['extra_context']['import_title'] = 'Import Trade Offers'
        return super(TradeOffersAdmin, self).changelist_view(*args, **kwargs)

    def get_urls(self):
        urls = super(TradeOffersAdmin, self).get_urls()
        custom_urls = [
            url(r'^(?i)import/$',
                self.admin_site.admin_view(self.import_trade),
                name='import_trade'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
        ]
        return custom_urls + urls

    def import_trade(self, request):
        ''' Import Shakti Trade offers '''
        form = UserImportForm()

        error_list = []
        if request.POST:
            dataset = Dataset()
            form = UserImportForm(request.POST, request.FILES)
            shakti_bonus = request.FILES['import_file']
            try:
                imported_data = dataset.load(shakti_bonus.read())
                import_obj = ImportOffers()
                error_list = import_obj.process_offers(request, imported_data)
            except StandardError as error:
                error_list = [error.message]
            if not error_list:
                return HttpResponseRedirect(reverse_lazy("admin:offers_tradeoffers_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Trade Offers',
            is_popup=False,
            to_field='',
            error_list=error_list,
            refaral_url='/admin/offers/tradeoffers',
            refaral_name='Trade Offers',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            action_form=form,
            form=form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/offers/import.html',
            context,
        )

    def sample_export_csv(self, request):
        ''' Sample CSV file '''
        return ImportOffers().sample_export_csv(TRADE_OFFERS_FIELDS,
                                                'trade_offers_sample.csv')

    def get_delete_url(self, obj):
        html = generate_delete_html(self, obj)
        return html
    get_delete_url.short_description = 'Action'


class DiscountToshaktiAdmin(CustomAdminTitle):
    model = DiscountToShakti
    list_display = ('id', 'name', 'start', 'end', 'discount', 'regional_distributor', 'get_delete_url')
    search_fields = ['name', 'start', 'end', 'discount',  'regional_distributor__user__name']

    fieldsets = (
        (None, {
            'fields': ('name', 'regional_distributor', 'start',
                       'end', 'discount'),

        }),
    )
    distributor_fieldsets = (
        (None, {
            'fields': ('name', 'start',
                       'end', 'discount'),

        }),
    )
    change_list_template = "admin/offers/change_list.html"
    actions = ['export_offers_list']

    def has_add_permission(self, request):
        try:
            distributor = request.user.regionaldistributor
        except ObjectDoesNotExist:
            distributor = False

        if distributor and self.get_queryset(request).count() > 0:
            return False
        return True

    def export_offers_list(self, request, queryset):
        data_headers = [
            'Name', 'Start Date (mm/dd/yyyy)', 'Expires on (mm/dd/yyyy)', 'Discount', 'Redistribution Stockist']
        data = tablib.Dataset(headers=data_headers, title='Discount to Shakti')

        for trade in queryset:
            start = trade.start.strftime('%m/%d/%Y')
            end = trade.end.strftime('%m/%d/%Y')

            row = [trade.name, start, end, trade.discount, trade.regional_distributor.user.name]

            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="Shakti Discount.xls"'
        response.write(data.export('xls'))
        return response
    export_offers_list.short_description = 'Export Discount to Shakti'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['export_title'] = 'Export Discount to Shakti'
        return super(DiscountToshaktiAdmin, self).changelist_view(*args, **kwargs)

    def get_delete_url(self, obj):
        html = generate_delete_html(self, obj)
        return html
    get_delete_url.short_description = 'Action'

    def get_fieldsets(self, request, obj=None):
        if not request.user.is_superuser:
            return self.distributor_fieldsets
        return super(DiscountToshaktiAdmin, self).get_fieldsets(request, obj)

    def get_queryset(self, request):
        queryset = super(DiscountToshaktiAdmin, self).get_queryset(request).\
            select_related('regional_distributor')

        if not request.user.is_superuser:
            distributor = RegionalDistributor.objects.get(user=request.user)
            queryset = queryset.filter(regional_distributor=distributor)
        return queryset

    def save_model(self, request, obj, form, change):

        if not change and hasattr(request.user, 'regionaldistributor'):
            distributor = RegionalDistributor.objects.get(user=request.user)
            obj.regional_distributor = distributor
            obj.regional_distributor_id = distributor.user_id
        try:
            super(DiscountToshaktiAdmin, self).save_model(
                request, obj, form, change)
        except IntegrityError as error:
            messages.add_message(request, messages.ERROR,
                                 'Please update the already added discount.')

            return HttpResponseRedirect(request.build_absolute_uri())

    def change_view(self, request, object_id, extra_context=None):
        ''' customize add/edit form '''
        extra_context = extra_context or {}
        try:
            distributor = request.user.regionaldistributor
        except ObjectDoesNotExist:
            distributor = False

        if distributor:
            extra_context['show_save_and_add_another'] = False

        return super(DiscountToshaktiAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def add_view(self, request, extra_context=None):
        ''' customize add/edit form '''
        extra_context = extra_context or {}
        try:
            distributor = request.user.regionaldistributor
        except ObjectDoesNotExist:
            distributor = False

        if distributor:
            extra_context['show_save_and_add_another'] = False
        return super(DiscountToshaktiAdmin, self).add_view(request, extra_context=extra_context)


admin.site.register(ShaktiPromotions, ShaktiPromotionsAdmin)
admin.site.register(ShaktiBonusAll, BonusAllAdmin)
admin.site.register(ShaktiBonus, BonusAdmin)
# admin.site.register(ShaktiOffers, ShaktiOffersAdmin)
admin.site.register(TradeOffers, TradeOffersAdmin)
admin.site.register(DiscountToShakti, DiscountToshaktiAdmin)
