'''Cms Module'''
from django.contrib import admin
from django.conf import settings
from django.utils.text import slugify
from hul.utility import CustomAdminTitle
from cms.models import CmsPage

# Register your models here.

class CmsPageAdmin(CustomAdminTitle):
    """
    custom Admin Class for Privacy model
    """
    list_display = ['title', 'slug', 'create_date']
    search_fields = ['title', 'slug']
    list_per_page = settings.ADMIN_PAGE_SIZE
    prepopulated_fields = {'slug': ('title',)}
    @classmethod
    def has_add_permission(cls, request):
        return False

    @classmethod
    def has_delete_permission(cls, request, obj=None):
        # Disable delete
        return False
    def save_model(self, request, obj, form, change):
        # don't overwrite manually set slug
        if form.cleaned_data['slug'] == "":
            obj.slug = slugify(obj.title)
        else:
            obj.slug = slugify(obj.slug)
        obj.save()

admin.site.register(CmsPage, CmsPageAdmin)
