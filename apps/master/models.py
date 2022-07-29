'''
models for master app
'''
from django.db import models


# Create your models here.
class Country(models.Model):
    """
    model for country
    """
    name = models.CharField(max_length=200)
    phone_code = models.CharField(max_length=10, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        """
        inner class
        """
        verbose_name_plural = "Countries"
