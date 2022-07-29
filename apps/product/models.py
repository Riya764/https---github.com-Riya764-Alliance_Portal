# -*- coding: utf-8 -*-
'''model.py products'''
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.safestring import mark_safe
from django.utils.encoding import python_2_unicode_compatible
from s3direct.fields import S3DirectField
from hul.utility import TimeStamped
from app.models import AlliancePartner
from localization.models import MeasurementUnit


@python_2_unicode_compatible
class Category(TimeStamped):
    """
    model for Products Ocassions
    """
    name = models.CharField(
        max_length=30, help_text='Note: Maximum 30 character(s).')
    short_description = models.CharField(blank=True, max_length=250,
                                         help_text='Note: Maximum 250 character(s).')
    logo = S3DirectField(dest='category_images', help_text='Image Size should not more than 100kb.',
                         null=True, blank=True)
    sort_order = models.IntegerField(default=1)

    def __str__(self):
        return self.name

    def thumbnail(self):
        '''Return Logo'''
        if self.logo:
            return """<img border="0"
            alt="Error" src="%s" height="50" />
            """ % (self.logo)
        else:
            return 'Image Not Uploaded'

    thumbnail.allow_tags = True
    thumbnail.short_description = 'Category Image'

    class Meta:
        """inner class"""
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'


class ProductsManager(models.Manager):

    def get_queryset(self):
        queryset = super(ProductsManager, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


@python_2_unicode_compatible
class Product(TimeStamped):
    """
    model for Products
    """
    category = models.ForeignKey(Category, verbose_name="Category",)
    brand = models.ForeignKey(AlliancePartner)
    partner_code = models.CharField(max_length=50)
    hsn_code = models.CharField(max_length=50)
    basepack_name = models.CharField(max_length=50)
    basepack_code = models.CharField(max_length=50)
    basepack_size = models.CharField(max_length=50)
    unit = models.ForeignKey(MeasurementUnit, verbose_name="Unit",)
    sku_code = models.CharField(
        max_length=50, verbose_name="SKU", null=True, blank=True)
    expiry_day = models.IntegerField(
        verbose_name='Expire in(days)', null=True, blank=True)
    cld_configurations = models.IntegerField(validators=[MinValueValidator(1)])
    cld_rate = models.FloatField(verbose_name=mark_safe(u"CLD Rate (₹)"),
                                 null=True, blank=True, default=0)
    mrp = models.FloatField(verbose_name=mark_safe(u"MRP (₹)"),
                            validators=[MinValueValidator(0.9), MaxValueValidator(10000.99)])
    tur = models.FloatField(verbose_name=mark_safe(u"TUR (₹)"), default=1,
                            validators=[MinValueValidator(0.9), MaxValueValidator(10000.99)])
    net_rate = models.FloatField(verbose_name=mark_safe(u"Invoice Price (₹)"), default=1,
                                 validators=[MinValueValidator(0.9), MaxValueValidator(10000.99)])
    base_rate = models.FloatField(verbose_name=mark_safe(u"Base Price (₹)"), default=1,
                                  validators=[MinValueValidator(0.9), MaxValueValidator(10000.99)])
    cgst = models.FloatField(verbose_name=mark_safe(u"CGST (%)"), default=0,
                             validators=[MinValueValidator(0), MaxValueValidator(99)])
    sgst = models.FloatField(verbose_name=mark_safe(u"SGST (%)"), default=0,
                             validators=[MinValueValidator(0), MaxValueValidator(99)])
    igst = models.FloatField(verbose_name=mark_safe(u"IGST (%)"), default=0,
                             validators=[MinValueValidator(0), MaxValueValidator(99)])
    cgst_amount = models.FloatField(verbose_name=mark_safe(u"CGST Amount (₹)"), default=0,
                                    validators=[MinValueValidator(0), MaxValueValidator(10000.99)])
    sgst_amount = models.FloatField(verbose_name=mark_safe(u"SGST Amount (₹)"), default=0,
                                    validators=[MinValueValidator(0), MaxValueValidator(10000.99)])
    igst_amount = models.FloatField(verbose_name=mark_safe(u"IGST Amount (₹)"), default=0,
                                    validators=[MinValueValidator(0), MaxValueValidator(10000.99)])
    image = S3DirectField(dest='product_images', help_text='Image Size\
                                      should not more than 300kb.', blank=True, null=True)
    # en_code = models.CharField(max_length=50, null=True, blank=True)
    objects = models.Manager()
    active_products = ProductsManager()

    def __str__(self):
        # return '{0} - {1}'.format(self.pk, self.basepack_name)
        return str(self.basepack_name)

    def thumbnail(self):
        '''Return Thumbnail'''
        if self.image:
            return """<img border="0"
            alt="Product Image" src="%s" height="50" />
            """ % (self.image)
        else:
            return 'Image Not Uploaded'

    thumbnail.allow_tags = True
    thumbnail.short_description = 'Product Image'

    def save(self, *args, **kwargs):
        price = round(self.base_rate + (self.base_rate *
                      self.brand.stockist_margin / 100), 5)

        self.cgst_amount = self.calculate_amount(price, self.cgst)
        self.sgst_amount = self.calculate_amount(price, self.sgst)
        self.igst_amount = self.calculate_amount(price, self.igst)

        self.net_rate = round(self.base_rate + self.cgst_amount +
                              self.sgst_amount + self.igst_amount, 5)

        self.tur = round(price + self.cgst_amount +
                         self.sgst_amount + self.igst_amount, 5)
        self.cld_rate = round(
            float(self.cld_configurations) * float(self.tur), 5)

        return super(Product, self).save(*args, **kwargs)

    def calculate_amount(self, amount, percent):
        '''
        calculate amount from tax perecentage
        '''
        return round(float(amount) * float(percent) / 100.0, 5)


@python_2_unicode_compatible
class ProductChild(TimeStamped):
    mother_basepack_code = models.ForeignKey(Product, max_length=50)
    child_basepack_code = models.CharField(max_length=50)
    en_code = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        # return '{0} - {1}'.format(self.pk, self.basepack_name)
        return str(self.child_basepack_code)


@python_2_unicode_compatible
class ProductImages(TimeStamped):
    """
    model for Products
    """
    product = models.ForeignKey(Product, related_name='product')
    image = S3DirectField(dest='product_images', null=True, blank=True,
                          help_text='Image Size should not more than 300kb.')
    sort_order = models.IntegerField(default=1)

    class Meta:
        """inner class"""
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'

    def __str__(self):
        return ''
