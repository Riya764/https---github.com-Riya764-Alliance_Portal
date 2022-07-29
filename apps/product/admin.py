'''Product Custom file'''
import tablib
from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
from django.db.models.fields.files import FileField
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from product.models import ProductChild

from hul.utility import CustomAdminTitle
from hul.settings.common import ADMIN_PAGE_SIZE
from product.models import Category, Product, ProductImages
from product.conf import PRODUCT_FIELDS
from product.import_products import ImportProduct
from app.import_users import ImportProcess
from app.forms import UserImportForm

######################################################
# Product Category
######################################################


class CategoryImageWidget(AdminFileWidget):
    '''
    Category Custom Image thumbnail widget...
    '''

    def render(self, name, value, attrs=None):
        output = []
        flag = False
        if value and getattr(value, "url", None):
            image_url = value.url
            image_url = image_url
            output.append(u' <a href="%s" target="_blank"><img style="max-width: 250px;"\
            src="%s"/></a> ' % (image_url, image_url))
            file_field = FileField()
            file_field.name = image_url
            file_field.path = value.path
            file_field.url = '/media/' + value.name
            file_field.model = Category
            flag = True

        if flag:
            output.append(super(CategoryImageWidget, self).render(
                name, file_field, attrs))
        else:
            output.append(super(CategoryImageWidget,
                                self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class CategoryAdmin(CustomAdminTitle):
    """
    Custom Admin Class for Category model
    """
    list_display = ['name', 'thumbnail', 'sort_order', 'is_active']
    list_select_related = []
    search_fields = ['name', 'short_description']
    list_per_page = ADMIN_PAGE_SIZE

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(CategoryAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'logo':
            kwargs.pop("request", None)
            kwargs['widget'] = CategoryImageWidget
            return db_field.formfield(**kwargs)
        return super(CategoryAdmin, self).formfield_for_dbfield(db_field, **kwargs)

######################################################
# Products
######################################################


class ProductInlineImageWidget(AdminFileWidget):
    '''
    Product Inline Image show thumbnail widget..
    '''

    def render(self, name, value, attrs=None):
        output = []
        flag = False
        if value and getattr(value, "url", None):
            image_url = value.url
            image_url = image_url
            output.append(u' <a href="%s" target="_blank"><img style="width:100px;"\
            src="%s"/></a> ' % (image_url, image_url))
            file_field = FileField()
            file_field.name = image_url
            file_field.path = value.path
            file_field.url = '/media/' + value.name
            file_field.model = ProductImages
            flag = True

        if flag:
            output.append(super(ProductInlineImageWidget,
                                self).render(name, file_field, attrs))
        else:
            output.append(super(ProductInlineImageWidget,
                                self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class ProductImagesInline(admin.TabularInline):
    '''
    Custom Product Image to show in Inline Product Model
    '''
    model = ProductImages
    fields = ("sort_order", "image", "is_active")
    verbose_name = "Image"
    verbose_name_plural = "Product Images"
    min_num = 1
    extra = 0
    show_change_link = False

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'image':
            kwargs.pop("request", None)
            kwargs['widget'] = ProductInlineImageWidget
            return db_field.formfield(**kwargs)
        return super(ProductImagesInline, self).formfield_for_dbfield(db_field, **kwargs)


class ProductImageWidget(AdminFileWidget):
    '''
    Custom Image Widget to show image thubmnail in form
    '''

    def render(self, name, value, attrs=None):
        output = []
        flag = False
        if value and getattr(value, "url", None):
            image_url = value.url
            image_url = image_url
            output.append(u' <a href="%s" target="_blank"><img style="width:100px;"\
            src="%s"/></a> ' % (image_url, image_url))
            file_field = FileField()
            file_field.name = image_url
            file_field.path = value.path
            file_field.url = '/media/' + value.name
            file_field.model = Product
            flag = True

        if flag:
            output.append(super(ProductImageWidget, self).render(
                name, file_field, attrs))
        else:
            output.append(super(ProductImageWidget,
                                self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class ProductAdmin(CustomAdminTitle):
    """
    custom Admin Class for Products model
    """
    list_display = ['basepack_name', 'basepack_code', 'thumbnail',
                    'category', 'brand', 'hsn_code', 'mrp', 'is_active']
    search_fields = ['basepack_name', 'basepack_code', 'brand__code',
                     'brand__user__name', 'category__name', 'mrp', ]
    list_select_related = ['brand__user', 'category', 'brand']

    fieldset = (
        (None, {'fields': ('category', 'brand', 'partner_code',
                           'basepack_name', 'basepack_code', "en_code", 'hsn_code', 'basepack_size',
                           'unit', 'sku_code', 'expiry_day', 'mrp', 'tur',
                           'net_rate', 'base_rate',  'cgst', 'sgst', 'igst',
                           'cgst_amount', 'sgst_amount', 'igst_amount',
                           'cld_configurations', 'cld_rate',
                           'get_retailer_margin',
                           'image', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('category', 'brand', 'partner_code', 'basepack_name',
                       'basepack_code', 'hsn_code', 'basepack_size', 'unit', 'sku_code',
                       'expiry_day', 'mrp', 'tur', 'base_rate', 'cgst', 'sgst',
                       'igst',
                       'cld_configurations', 'image', 'is_active')}),
    )
    list_filter = ['brand', 'category', ]
    list_per_page = ADMIN_PAGE_SIZE
    inlines = [ProductImagesInline]
    change_list_template = "admin/product/change_list.html"
    readonly_fields = ['cld_rate', 'tur', 'net_rate', 'cgst_amount', 'sgst_amount',
                       'igst_amount', 'get_retailer_margin']

    actions = ['activate_product',
               'deactivate_product', 'export_products_list']

    def export_products_list(self, request, queryset):
        data_headers = ['CATEGORY', 'BRAND CODE', 'BASEPACK NAME', 'BASEPACK CODE', 'EN_CODE', 'BASEPACK SIZE',
                        'UNIT', 'EXPIRY IN(DAYS)', 'CLD CONFIGURATION', 'MRP', 'Base Price', 'CGST (%)',
                        'SGST (%)', 'IGST (%)', 'HSN CODE', 'IS ACTIVE']
        data = tablib.Dataset(headers=data_headers)

        for product in queryset:
            row = (str(product.category), str(product.brand), product.basepack_name,
                   product.basepack_code, product.en_code, product.basepack_size, str(
                       product.unit), product.expiry_day,
                   product.cld_configurations, product.mrp, product.base_rate, product.cgst,
                   product.sgst, product.igst, product.hsn_code, 'Yes' if product.is_active else 'No')
            data.append(tuple(row))
        # for product in queryset:
        #     row = (str(product.category), str(product.brand), product.basepack_name,
        #            product.basepack_code,  product.basepack_size, str(
        #                product.unit), product.expiry_day,
        #            product.cld_configurations, product.mrp, product.base_rate, product.cgst,
        #            product.sgst, product.igst, product.hsn_code, 'Yes' if product.is_active else 'No')
        #     data.append(tuple(row))

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="products.xls"'
        response.write(data.export('xls'))
        return response
    export_products_list.short_description = 'Export Products'

    class Media:
        '''
        adding custom media to admin
        '''
        js = ('/static/admin/product/js/product.js',)

    def get_retailer_margin(self, obj=None):
        margin = 'NA'
        if obj:
            margin = obj.brand.stockist_margin
        return margin
    get_retailer_margin.short_description = 'Retailer Margin (in %)'

    def deactivate_product(self, request, queryset):
        '''
        Custom function to Deactivate Products action
        '''
        queryset.update(is_active=False)
        self.message_user(
            request, "Selected product(s) deactivated successfully.")
    deactivate_product.short_description = "Deactivate selected product(s)"

    def changelist_view(self, *args, **kwargs):
        kwargs['extra_context'] = kwargs.get('extra_context', {})
        kwargs['extra_context']['import_title'] = 'Bulk Import Products'
        kwargs['extra_context']['export_title'] = 'Export Products'
        return super(ProductAdmin, self).changelist_view(*args, **kwargs)

    def activate_product(self, request, queryset):
        '''
        Custom functon to activate product action
        '''
        queryset.update(is_active=True)
        self.message_user(
            request, "Selected product(s) activated successfully.")
    activate_product.short_description = "Activate selected product(s)"

    def get_readonly_fields(self, request, obj=None):
        readony_list = list(self.readonly_fields) or []

        # hasattr(request.user,'regionaldistributor')
        if not request.user.is_superuser:
            for field in self.opts.local_fields:
                if field.name not in readony_list:
                    readony_list.append(field.name)
        return readony_list

    def get_actions(self, request):
        '''Remove all delete action'''

        actions = super(ProductAdmin, self).get_actions(request)
        # del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()
        custom_urls = [
            url(r'^import/$',
                self.admin_site.admin_view(self.import_product),
                name='import_products'),
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
        return ImportProcess().sample_export_csv(PRODUCT_FIELDS,
                                                 'products_sample_file.csv')

    def sample_export_xlsx(self, *args, **kwargs):
        ''' SAMPLE XLSX file '''
        return ImportProcess().sample_export_xlsx(PRODUCT_FIELDS,
                                                  'products_sample_file.xlsx')

    def import_product(self, request):
        ''' Import Sales Users '''
        form = UserImportForm()
        import_process = ImportProcess()
        import_product = ImportProduct()
        error_list = []
        if request.POST:
            try:
                form = UserImportForm(request.POST, request.FILES)
                import_file = import_process.store_import_file(
                    request.FILES['import_file'])
                import_product.save_import_file(
                    request, import_file)
            except StandardError as error:
                error_list = [error.message]
            if not error_list:
                return HttpResponseRedirect(reverse("admin:product_product_changelist"))

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form

        context = dict(
            self.admin_site.each_context(request),
            title='Import Products',
            is_popup=False,
            to_field='',
            cl=self,
            has_add_permission=self.has_add_permission(request),
            opts=self.opts,
            action_form=form,
            error_list=error_list,
            form=form,
            actions_on_top=self.actions_on_top,
            actions_on_bottom=self.actions_on_bottom,
            actions_selection_counter=self.actions_selection_counter,
            preserved_filters=self.get_preserved_filters(request),
        )

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            'admin/product/import.html',
            context,
        )

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'image':
            kwargs.pop("request", None)
            kwargs['widget'] = ProductImageWidget
            return db_field.formfield(**kwargs)
        return super(ProductAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def get_queryset(self, request):
        if not request.user.is_superuser:
            queryset = super(ProductAdmin, self).get_queryset(request)
            return queryset.filter(brand__user=request.user)
        else:
            return super(ProductAdmin, self).get_queryset(request)

    def get_fieldsets(self, request, obj=None):

        if obj is not None:
            return self.fieldset
        return self.add_fieldsets


admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductChild)
