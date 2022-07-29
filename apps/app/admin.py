'''
app/admin.py
'''
import tablib
from django.contrib import admin
from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.utils import timezone as dt

from django.template.context import Context
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.contrib.auth.models import Group

from import_export import widgets, fields, resources
from import_export.admin import ImportExportModelAdmin, ExportMixin, ImportMixin
from import_export.formats import base_formats

from oauth2_provider.models import AccessToken, Application, Grant, RefreshToken


from hul.constants import FROM_EMAIL, ALLIANCE_EMAIL_SUBJECT, ADMIN_EMAIL
from hul.settings.common import ADMIN_SITE_HEADER, ADMIN_SITE_TITLE
from hul.custom_admin_user import UserAdmin
from hul.utility import CustomAdminTitle

from app.import_users import ImportProcess
from app.conf import (SHAKTI_FIELDS, SALES_USER_FIELDS,
                      RD_USER_FIELDS, ALLIANCE_USER_FIELDS)
from app.models import (User, AlliancePartner, RegionalDistributor,
                        ShaktiEntrepreneur, RegionalSalesPromoter,
                        DistributorNorm)
from app.constants import (ALLIANCE_GROUP, DISTRIBUTER_GROUP,
                           REGIONAL_SALES_PROMOTER, SHAKTI_ENTERPRENEUR)
from app.forms import (UserImportForm, AddUserForm, UserChangeForm, RSPUserChangeForm, DistributorNormForm,
                        AddRspUserForm, AddRegionalDistributorForm, AddShaktiform,
                        ChangeRegionalDistributorForm, ChangeShaktiform)
from job.models import Email
from product.models import Product

#=========================================================================
# Set headers and title
#=========================================================================
AdminSite.site_header = ADMIN_SITE_HEADER
AdminSite.site_title = ADMIN_SITE_TITLE


class AlliancePartnerAdmin(CustomAdminTitle):
    ''' Alliance Partner Admin Custom Class'''
    add_form = AddUserForm
    model = AlliancePartner
    form = UserChangeForm
    group_type = ALLIANCE_GROUP

    change_list_template = "admin/app/change_list.html"

    list_display = ['user', 'thumbnail', 'code', 'address', 'is_active']
    list_display_links = ['user', ]
    list_select_related = ['user', 'address', 'address__state', 'address__country']
    search_fields = ['user__name', 'user__username', 'user__email', 'code',
                     'address__address_line1', 'address__address_line2',
                     'address__address_line3', 'address__city', 'address__state__name', ]
    actions = ['activate_user', 'deactivate_user', 'export_user_list']

    '''Remove delete action in action bar'''

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import Alliance Partner'
        kwargs['extra_context']['export_title'] = 'Export Alliance Partner'
        return super(AlliancePartnerAdmin, self).changelist_view(*args, **kwargs)

    def get_actions(self, request):
        actions = super(AlliancePartnerAdmin, self).get_actions(request)
        #del actions['delete_selected']
        return actions

    def export_user_list(self, request, queryset):
        data_headers = ['NAME', 'EMAIL', 'USERNAME', 'CONTACT NUMBER', 'ADDRESS LINE1', 'ADDRESS LINE2',
                        'ADDRESS LINE3', 'STATE', 'CITY', 'POSTCODE', 'CODE']
        data = tablib.Dataset(headers=data_headers, title='Alliance Partners')

        for alliance in queryset:
            row = (alliance.user.name, alliance.user.email, alliance.user.username, alliance.user.contact_number,
                   alliance.address.address_line1, alliance.address.address_line2, alliance.address.address_line3,
                   str(alliance.address.state), alliance.address.city, alliance.address.post_code, alliance.code)
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="alliances.xls"'
        response.write(data.export('xls'))
        return response
    export_user_list.short_description = 'Export Alliance'

    def deactivate_user(self, request, queryset):
        '''Deactivate user custom action bar'''
        queryset.update(is_active=False)
        self.message_user(
            request, "Selected record(s) deactivated successfully.")

    deactivate_user.short_description = "Deactivate selected users(s)"

    def activate_user(self, request, queryset):
        '''Activate user custom action bar'''
        queryset.update(is_active=True)
        self.message_user(
            request, "Selected record(s) activated successfully.")

    activate_user.short_description = "Activate selected users(s)"

    def get_default_group(self):
        '''Get default Groups'''
        try:
            return Group.objects.filter(name__iexact=self.group_type).get()
        except Group.DoesNotExist:
            return False

    def save_model(self, request, obj, form, change):
        if form.data['email'] and 'password' in form.data:
            context = Context({'url': 'http:// %s' % (request.get_host()),
                               'name': form.data['name'], 'username': form.data['username'],
                               'password': form.data['password']})
            html_content = render_to_string(
                'app/add_alliance_email.html', context)
            Email.objects.create(to_email=form.data['email'],
                                 from_email=FROM_EMAIL,
                                 subject=ALLIANCE_EMAIL_SUBJECT,
                                 message=html_content)

        data = super(AlliancePartnerAdmin, self).save_model(
            request, obj, form, change)
        if not change:
            group = self.get_default_group()
            if group:
                group.user_set.add(obj.user)
        return data

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super(AlliancePartnerAdmin, self).get_form(request, obj, **defaults)

    def get_urls(self):
        urls = super(AlliancePartnerAdmin, self).get_urls()
        custom_urls = [
            url(r'^import/$',
                self.admin_site.admin_view(self.import_alliancepartner),
                name='import_alliancepartner'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
            url(r'^import/sample_export_xlsx/$',
                self.admin_site.admin_view(self.sample_export_xlsx),
                name='sample_export_xlsx'),
        ]
        return custom_urls + urls

    def sample_export_csv(self, *args, **kwargs):
        ''' Sample CSV file '''
        return ImportProcess().sample_export_csv(ALLIANCE_USER_FIELDS,
                                                 'alliance-sample_file.csv')

    def sample_export_xlsx(self, *args, **kwargs):
        ''' SAMPLE XLSX file '''
        return ImportProcess().sample_export_xlsx(ALLIANCE_USER_FIELDS,
                                                  'alliance-sample_file.xlsx')

    def import_alliancepartner(self, request):
        ''' Import Alliance Users '''
        form = UserImportForm()
        import_process = ImportProcess()
        error_list = []
        if request.POST:
            form = UserImportForm(request.POST, request.FILES)
            import_file = import_process.store_import_file(
                request.FILES['import_file'])
            error_list = import_process.save_import_file(
                request, import_file, ALLIANCE_GROUP, ALLIANCE_USER_FIELDS)

            if not error_list:
                return HttpResponseRedirect(reverse("admin:app_alliancepartner_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form

        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Alliance Partner',
            is_popup=False,
            to_field='',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            action_form=form,
            form=form,
            error_list=error_list,
            refaral_url='/admin/app/alliancepartner',
            refaral_name='Alliance Partner',
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/app/import.html',
            context,
        )


class DistributorUserAdmin(CustomAdminTitle):
    '''Class for RD RegionalDistributor'''
    add_form = AddRegionalDistributorForm
    model = RegionalDistributor
    form = ChangeRegionalDistributorForm
    group_type = DISTRIBUTER_GROUP
    change_list_template = "admin/app/change_list.html"

    list_display = ['user', 'thumbnail', 'code', 'address', 'is_active']
    list_display_links = ['user', ]
    list_select_related = ['user', 'address', 'address__state', 'address__country']
    search_fields = ['user__name', 'user__username', 'user__email', 'code',
                     'address__address_line1', 'address__address_line2',
                     'address__address_line3', 'address__city', 'address__state__name', ]
    filter_horizontal = ['alliance_partner', ]
    list_filter =['alliance_partner',]
    actions = ['activate_user', 'deactivate_user', 'export_user_list']

    def export_user_list(self, request, queryset):
        data_headers = ['NAME', 'EMAIL', 'USERNAME', 'CONTACT NUMBER', 'ADDRESS LINE1', 'ADDRESS LINE2',
                        'ADDRESS LINE3', 'STATE', 'CITY', 'POSTCODE', 'CODE', 'ORDER DAY', 'MINIMUM ORDER',
                        'Alliance Distribution Channel', 'Alliance Division', 'Alliance Plant', 'GST Code', 'HUL Code']
        data = tablib.Dataset(headers=data_headers,
                              title='Regional Distributors')

        for distributor in queryset:
            row = (distributor.user.name, distributor.user.email, distributor.user.username, distributor.user.contact_number,
                   distributor.address.address_line1, distributor.address.address_line2, distributor.address.address_line3,
                   str(distributor.address.state), distributor.address.city, distributor.address.post_code,
                   distributor.code, distributor.get_order_day_display().capitalize(),
                   distributor.min_order, distributor.ap_dist_channel, distributor.ap_division,
                   distributor.ap_plant, distributor.gst_code, distributor.hul_code)
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="distributor.xls"'
        response.write(data.export('xls'))
        return response
    export_user_list.short_description = 'Export Redistribution Stockist'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import Redistribution Stockist'
        kwargs['extra_context']['export_title'] = 'Export Redistribution Stockist'

        return super(DistributorUserAdmin, self).changelist_view(*args, **kwargs)

    def get_actions(self, request):
        actions = super(DistributorUserAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def deactivate_user(self, request, queryset):
        '''Deactivate user action bar'''
        queryset.update(is_active=False)
        self.message_user(
            request, "Selected record(s) deactivated successfully.")

    deactivate_user.short_description = "Deactivate selected users(s)"

    def activate_user(self, request, queryset):
        '''Action bar to activate user'''
        queryset.update(is_active=True)
        self.message_user(
            request, "Selected record(s) activated successfully.")

    activate_user.short_description = "Activate selected users(s)"

    def get_default_group(self):
        '''Get default Group by name'''
        try:
            return Group.objects.filter(name__iexact=self.group_type).get()
        except Group.DoesNotExist:
            return False

    def save_model(self, request, obj, form, change):
        if form.data['email'] and 'password' in form.data:
            context = Context({'url': 'http:// %s' % (request.get_host()),
                               'name': form.data['name'],
                               'username': form.data['username'],
                               'password': form.data['password']})
            html_content = render_to_string('app/add_rd_email.html', context)
            Email.objects.create(to_email=form.data['email'],
                                 from_email=FROM_EMAIL,
                                 subject=ALLIANCE_EMAIL_SUBJECT,
                                 message=html_content)

        data = super(DistributorUserAdmin, self).save_model(
            request, obj, form, change)

        if not change:
            group = self.get_default_group()
            if group:
                group.user_set.add(obj.user)
        return data

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        form =  super(DistributorUserAdmin, self).get_form(request, obj, **defaults)
        
        # if obj:
        #     form.fields["alliance_partner"].queryset = AlliancePartner.active_ap.all()
        return form


    def get_queryset(self, request):
        queryset = super(DistributorUserAdmin, self).get_queryset(request)

        if not request.user.is_superuser:
            return queryset.filter(alliance_partner__user=request.user)
        return queryset

    def get_urls(self):
        urls = super(DistributorUserAdmin, self).get_urls()
        custom_urls = [
            url(r'^import/$',
                self.admin_site.admin_view(self.import_regionaldistributor),
                name='import_regionaldistributor'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
            url(r'^import/sample_export_xlsx/$',
                self.admin_site.admin_view(self.sample_export_xlsx),
                name='sample_export_xlsx'),
        ]
        return custom_urls + urls

    def sample_export_csv(self, *args, **kwargs):
        ''' Sample CSV file '''
        return ImportProcess().sample_export_csv(RD_USER_FIELDS,
                                                 'RedistributionStockist_sample_file.csv')

    def sample_export_xlsx(self, *args, **kwargs):
        ''' SAMPLE XLSX file '''
        return ImportProcess().sample_export_xlsx(RD_USER_FIELDS,
                                                  'RedistributionStockist_sample_file.xlsx')

    def import_regionaldistributor(self, request):
        ''' Import Distributor Users '''

        form = UserImportForm()
        import_process = ImportProcess()
        error_list = []
        if request.POST:
            form = UserImportForm(request.POST, request.FILES)
            import_file = import_process.store_import_file(
                request.FILES['import_file'])
            error_list = import_process.save_import_file(
                request, import_file, DISTRIBUTER_GROUP, RD_USER_FIELDS)

            if not error_list:
                return HttpResponseRedirect(reverse("admin:app_regionaldistributor_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form

        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Redistribution Stockists',
            is_popup=False,
            to_field='',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            action_form=form,
            error_list=error_list,
            refaral_url='/admin/app/regionaldistributor',
            refaral_name='Redistribution Stockists',
            form=form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/app/import.html',
            context,
        )


class SalesUserAdmin(CustomAdminTitle):
    '''Custom Sales User Class'''
    add_form = AddRspUserForm
    model = RegionalSalesPromoter
    form = RSPUserChangeForm
    group_type = REGIONAL_SALES_PROMOTER
    change_list_template = "admin/app/change_list.html"

    list_display = ['user', 'thumbnail', 'rsp_id', 'employee_number',
                    'address', 'regional_distributor', 'is_active']
    list_select_related = ['regional_distributor', 'user', 'address', 'address__state', 'address__country', 'regional_distributor__user']
    list_display_links = ['user', ]
    search_fields = ['user__name', 'user__username', 'user__email', 'rsp_id',
                     'address__address_line1', 'address__address_line2',
                     'address__address_line3', 'address__city', 'address__state__name',
                     'employee_number', 'regional_distributor__code']

    actions = ['activate_user', 'deactivate_user', 'export_user_list']

    def export_user_list(self, request, queryset):
        data_headers = ['NAME', 'EMAIL', 'USERNAME', 'CONTACT NUMBER', 'ADDRESS LINE1', 'ADDRESS LINE2',
                        'ADDRESS LINE3', 'STATE', 'CITY', 'POSTCODE', 'RSP ID', 'REDISTRIBUTION STOCKIST CODE', 'EMPLOYEE NUMBER']
        data = tablib.Dataset(headers=data_headers, title='RSPs')

        for salesuser in queryset:
            row = (salesuser.user.name, salesuser.user.email, salesuser.user.username, salesuser.user.contact_number,
                   salesuser.address.address_line1, salesuser.address.address_line2, salesuser.address.address_line3,
                   str(salesuser.address.state), salesuser.address.city, salesuser.address.post_code, salesuser.rsp_id,
                   str(salesuser.regional_distributor), salesuser.employee_number)
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="salesusers.xls"'
        response.write(data.export('xls'))
        return response
    export_user_list.short_description = 'Export RSPs'

    '''Remove Delete action in action bar'''

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import RSP'
        kwargs['extra_context']['export_title'] = 'Export RSP'
        return super(SalesUserAdmin, self).changelist_view(*args, **kwargs)

    def get_actions(self, request):
        actions = super(SalesUserAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def deactivate_user(self, request, queryset):
        '''Deactivate user action bar'''
        queryset.update(is_active=False)
        self.message_user(
            request, "Selected record(s) deactivated successfully.")

    deactivate_user.short_description = "Deactivate selected users(s)"

    def activate_user(self, request, queryset):
        '''Activate user action bar'''
        queryset.update(is_active=True)
        self.message_user(
            request, "Selected record(s) activated successfully.")

    activate_user.short_description = "Activate selected users(s)"

    def get_default_group(self):
        '''Get user default group'''
        try:
            return Group.objects.filter(name__iexact=self.group_type).get()
        except Group.DoesNotExist:
            return False

    def save_model(self, request, obj, form, change):
        if form.data['email'] and 'password' in form.data:
            context = Context({'url': 'http:// %s' % (request.get_host()),
                               'name': form.data['name'],
                               'username': form.data['username'],
                               'password': form.data['password']})

            html_content = render_to_string('app/add_rsp_email.html', context)
            Email.objects.create(to_email=form.data['email'],
                                 from_email=ADMIN_EMAIL,
                                 subject=ALLIANCE_EMAIL_SUBJECT,
                                 message=html_content)

        data = super(SalesUserAdmin, self).save_model(
            request, obj, form, change)
        if not change:
            user_obj = User.objects.get(pk=obj.user.pk)
            user_obj.is_staff = False
            user_obj.save()

            group = self.get_default_group()
            if group:
                group.user_set.add(obj.user)
        return data

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super(SalesUserAdmin, self).get_form(request, obj, **defaults)

    def get_queryset(self, request):
        if not request.user.is_superuser:
            queryset = super(SalesUserAdmin, self).get_queryset(request).\
                select_related('user', 'regional_distributor',)
            return queryset.filter(regional_distributor__user=request.user)
        else:
            return super(SalesUserAdmin, self).get_queryset(request)

    def get_urls(self):
        urls = super(SalesUserAdmin, self).get_urls()
        custom_urls = [
            url(r'^import/$',
                self.admin_site.admin_view(self.import_rsp),
                name='import_rsp'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
            url(r'^import/sample_export_xlsx/$',
                self.admin_site.admin_view(self.sample_export_xlsx),
                name='sample_export_xlsx'),
        ]
        return custom_urls + urls

    def sample_export_csv(self, *args, **kwargs):
        ''' Sample CSV file '''
        return ImportProcess().sample_export_csv(SALES_USER_FIELDS,
                                                 'rsp_sample_file.csv')

    def sample_export_xlsx(self, *args, **kwargs):
        ''' SAMPLE XLSX file '''
        return ImportProcess().sample_export_xlsx(SALES_USER_FIELDS,
                                                  'rsp_sample_file.xlsx')

    def import_rsp(self, request):
        ''' Import Sales Users '''
        form = UserImportForm()
        import_process = ImportProcess()
        error_list = []
        if request.POST:
            form = UserImportForm(request.POST, request.FILES)
            import_file = import_process.store_import_file(
                request.FILES['import_file'])
            error_list = import_process.save_import_file(
                request, import_file, REGIONAL_SALES_PROMOTER, SALES_USER_FIELDS)

            if not error_list:
                return HttpResponseRedirect(reverse("admin:app_regionalsalespromoter_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form

        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Regional Sales Promoter',
            is_popup=False,
            to_field='',
            error_list=error_list,
            refaral_url='/admin/app/regionalsalespromoter',
            refaral_name='RSPs',
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
            'admin/app/import.html',
            context,
        )


class ShaktiEntrepreneurAdmin(CustomAdminTitle):
    '''
    Shakti Entrepreneur Custom Class
    '''
    add_form = AddShaktiform
    model = ShaktiEntrepreneur
    form = ChangeShaktiform
    group_type = SHAKTI_ENTERPRENEUR
    change_list_template = "admin/app/change_list.html"

    list_display = ['user_name', 'thumbnail', 'regional_sales_name',
                    'code', 'beat_name', 'order_day', 'is_active']

    list_select_related = ['regional_sales', 'user', 'address', 'regional_sales__user']

    search_fields = ['user__name', 'user__username', 'user__email',
                     'code', 'address__address_line1', 'address__address_line2',
                     'address__address_line3', 'address__city', 'address__state__name',
                     'beat_name', 'regional_sales__rsp_id', 'regional_sales__employee_number',
                     'regional_sales__user__name']

    ap_readonly_fields = ['regional_sales', 'code', 'beat_name', 'order_day',
                          'address', 'user']

    actions = ['activate_user', 'deactivate_user', 'export_user_list']

    def export_user_list(self, request, queryset):
        data_headers = ['NAME', 'EMAIL', 'USERNAME', 'CONTACT NUMBER', 'ADDRESS LINE1', 'ADDRESS LINE2',
                        'ADDRESS LINE3', 'STATE', 'CITY', 'POSTCODE', 'PASSWORD', 'CODE', 'RSP ID', 'BEAT NAME', 'ORDER DAY',
                        'MINIMUM ORDER', 'IS ACTIVE']
        data = tablib.Dataset(headers=data_headers,
                              title='Shakti Entrepreneurs')

        for shakti in queryset:
            email = shakti.user.email if (
                shakti.user.email is not None and shakti.user.email != 'null') else ''
            row = (shakti.user.name, email, shakti.user.username, shakti.user.contact_number,
                   shakti.address.address_line1, shakti.address.address_line2, shakti.address.address_line3,
                   str(shakti.address.state), shakti.address.city, shakti.address.post_code, '',
                   shakti.code,
                   shakti.regional_sales.rsp_id, shakti.beat_name, shakti.get_order_day_display(
                   ).capitalize(), shakti.min_order,
                   shakti.is_active)
            data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="shaktientrepreneur_list.xlsx"'
        response.write(data.export('xlsx'))
        return response
    export_user_list.short_description = 'Export Shakti Enterpreneurs'

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import Shakti Entrepreneur'
        kwargs['extra_context']['export_title'] = 'Export Shakti Entrepreneur'
        return super(ShaktiEntrepreneurAdmin, self).changelist_view(*args, **kwargs)

    def get_actions(self, request):
        '''Remove object delete permissions'''
        actions = super(ShaktiEntrepreneurAdmin, self).get_actions(request)

        if 'delete_selected' in actions.keys():
            del actions['delete_selected']

        if hasattr(request.user, 'alliancepartner'):
            actions = []

        return actions

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields)
        if obj and hasattr(request.user, 'alliancepartner'):
            readony_list = self.ap_readonly_fields
        return readony_list

    def deactivate_user(self, request, queryset):
        '''
        Deactivate User Custom Action
        '''
        queryset.update(is_active=False)
        self.message_user(
            request, "Selected record(s) deactivated successfully.")

    deactivate_user.short_description = "Deactivate selected users(s)"

    def activate_user(self, request, queryset):
        '''
        Custom Action User Activate
        '''
        queryset.update(is_active=True)
        self.message_user(
            request, "Selected record(s) activated successfully.")

    activate_user.short_description = "Activate selected users(s)"

    '''Remove object delete permission'''

    def has_delete_permission(self, request, obj=None):
        return False

    def user_name(self, obj):
        '''Return User name'''
        return obj.user.name
    user_name.allow_tags = True
    user_name.short_description = 'User Name'

    def regional_sales_name(self, obj):
        ''' Regional Sales Promoter '''
        return obj.regional_sales.user.name
    regional_sales_name.allow_tags = True
    regional_sales_name.short_description = 'Rural Sale Promotor'

    def get_default_group(self):
        '''Custom user group permissions'''
        try:
            return Group.objects.filter(name__iexact=self.group_type).get()
        except Group.DoesNotExist:
            return False

    def save_model(self, request, obj, form, change):
        data = super(ShaktiEntrepreneurAdmin, self).save_model(
            request, obj, form, change)
        if not change:
            user_obj = User.objects.get(pk=obj.user.pk)
            user_obj.is_staff = False
            user_obj.save()
            group = self.get_default_group()
            if group:
                group.user_set.add(obj.user)
        return data

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super(ShaktiEntrepreneurAdmin, self).get_form(request, obj, **defaults)

    def get_queryset(self, request):
        user = request.user
        if not user.is_superuser:
            queryset = super(ShaktiEntrepreneurAdmin, self).get_queryset(request).\
                select_related('user', 'regional_sales',)

            if hasattr(user, 'alliancepartner'):
                user = user.alliancepartner.alliance_distributor_related.values_list(
                    'user_id', flat=True)
                queryset = queryset.filter(is_active=True)

            rsps = RegionalSalesPromoter.objects.filter(
                regional_distributor__user__in=list(user)).values_list('pk', flat=True)

            return queryset.filter(regional_sales_id__in=list(rsps))
        else:
            return super(ShaktiEntrepreneurAdmin, self).get_queryset(request)

    def get_urls(self):
        urls = super(ShaktiEntrepreneurAdmin, self).get_urls()
        custom_urls = [
            url(r'^(?i)import/$',
                self.admin_site.admin_view(self.import_shakti),
                name='import_shakti'),
            url(r'^import/sample_export_csv/$',
                self.admin_site.admin_view(self.sample_export_csv),
                name='sample_export_csv'),
            url(r'^import/sample_export_xlsx/$',
                self.admin_site.admin_view(self.sample_export_xlsx),
                name='sample_export_xlsx'),
        ]
        return custom_urls + urls

    def sample_export_csv(self, *args, **kwargs):
        ''' Sample CSV file '''
        return ImportProcess().sample_export_csv(SHAKTI_FIELDS,
                                                 'shaktientrepreneur_sample_file.csv')

    def sample_export_xlsx(self, *args, **kwargs):
        ''' SAMPLE XLSX file '''
        return ImportProcess().sample_export_xlsx(SHAKTI_FIELDS,
                                                  'shaktientrepreneur_sample_file.xlsx')

    def import_shakti(self, request):
        ''' Import Shakti Users '''
        form = UserImportForm()
        import_process = ImportProcess()
        error_list = []
        if request.POST:
            form = UserImportForm(request.POST, request.FILES)
            import_file = import_process.store_import_file(
                request.FILES['import_file'])
            error_list = import_process.save_import_file(
                request, import_file, SHAKTI_ENTERPRENEUR, SHAKTI_FIELDS)
            if not error_list:
                return HttpResponseRedirect(reverse("admin:app_shaktientrepreneur_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context = dict(
            self.admin_site.each_context(request),
            title='Bulk Import Shakti Enterpreneur',
            is_popup=False,
            to_field='',
            error_list=error_list,
            refaral_url='/admin/app/shaktientrepreneur',
            refaral_name='Shakti Enterpreneur',
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
            'admin/app/import.html',
            context,
        )


class CustomUserAdmin(UserAdmin):
    """
    Custom Admin class for Custom user model
    """
    list_select_related = True
    list_display = ['id', 'name', 'email', 'username', 'is_active', ]

    search_fields = ['email', 'name', 'id']


class DistributorNormResource(resources.ModelResource):

    distributor = fields.Field(column_name='distributor', attribute='distributor', 
                                widget=widgets.ForeignKeyWidget(RegionalDistributor, 'code'))
    product = fields.Field(column_name='product',attribute='product', widget=widgets.ForeignKeyWidget(Product, 'basepack_code'))
    # norm = fields.Field(column_name='Norm', attribute='norm')
    # distributor_code = fields.Field(readonly=True)
    # product_code = fields.Field(readonly=True)

    class Meta(object):
        model = DistributorNorm
        skip_unchanged = True
        raise_errors = False
        # fields = ('id', 'norm')
        exclude = ('is_active', 'created', 'modified',)
        export_order = ('id', 'distributor', 'product', 'norm', )

    # distributor = fields.Field(column_name='distributor_code', attribute='distributor',
    #                            widget=widgets.ForeignKeyWidget(RegionalDistributor, 'code'))
    # product = fields.Field(column_name='basepack_code', attribute='product',
    #                        widget=widgets.ForeignKeyWidget(Product, 'basepack_code'))

    # class Meta(object):
    #     model = DistributorNorm
    #     skip_unchanged = True
    #     raise_errors = False
    #     exclude = ('is_active', 'created', 'modified')
    #     export_order = ('id', 'distributor', 'product', 'norm')

    def dehydrate_distributor_code(self, distributornorm):
        return '{0} : {1}'.format(distributornorm.distributor.code, distributornorm.distributor.user.name)

    def dehydrate_product_code(self, distributornorm):
        return '{0} : {1}'.format(distributornorm.product.basepack_code, distributornorm.product.basepack_name)


class DistributorNormAdmin(CustomAdminTitle, ImportExportModelAdmin, ImportMixin, ExportMixin):
    resource_class = DistributorNormResource
    model = DistributorNorm
    list_display = ['id', 'distributor', 'product', 'norm']
    list_select_related = ['distributor__user', 'product']
    form = DistributorNormForm

    search_fields = ['distributor__user__name', 'id', 'product__basepack_name']

    fieldsets = (
        (None, {
            'fields': ('distributor', 'product', 'norm'),
        }),
    )

    formats = (
        base_formats.CSV,
        base_formats.XLS,
    )

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = self.formats
        return [f for f in formats if f().can_export()]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = self.formats
        return [f for f in formats if f().can_export()]


admin.site.register(User, CustomUserAdmin)
admin.site.register(RegionalDistributor, DistributorUserAdmin)
admin.site.register(AlliancePartner, AlliancePartnerAdmin)
admin.site.register(RegionalSalesPromoter, SalesUserAdmin)
admin.site.register(ShaktiEntrepreneur, ShaktiEntrepreneurAdmin)
admin.site.register(DistributorNorm, DistributorNormAdmin)

if not settings.DEBUG:
    from djcelery.models import (TaskState, WorkerState,
                                 PeriodicTask, IntervalSchedule, CrontabSchedule)

    admin.site.unregister(User)
    admin.site.unregister(Group)
    admin.site.unregister(AccessToken)
    admin.site.unregister(Grant)
    admin.site.unregister(RefreshToken)
    admin.site.unregister(Application)
    admin.site.unregister(TaskState)
    admin.site.unregister(WorkerState)
    admin.site.unregister(IntervalSchedule)
    admin.site.unregister(CrontabSchedule)
    admin.site.unregister(PeriodicTask)
