'''CMS models'''
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from tinymce.models import HTMLField

@python_2_unicode_compatible
class CmsPage(models.Model):
    '''cms model'''
    title = models.CharField(max_length=100)
    content = HTMLField()
    slug = models.SlugField(unique=True, max_length=40, null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
