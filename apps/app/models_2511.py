# -*- coding: utf-8 -*-
'''Django Imports'''
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import (PermissionsMixin,
                                        BaseUserManager,
                                        AbstractBaseUser)
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.utils.safestring import mark_safe
from django.core.validators import MinValueValidator, MaxValueValidator
from s3direct.fields import S3DirectField

from hul.choices import AddressType, OrderDay, OtpStatusType
from hul.utility import TimeStamped
from localization.models import State, Country


#=========================================================================
# Model for Custom User
#=========================================================================
class CustomUserManager(BaseUserManager):
    """
    for handling create user for user model
    """
    use_in_migrations = True

    def _create_user(self, username, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        username = self.normalize_email(username)
        user = self.model(username=username,
                          is_staff=is_staff,
                          is_active=True,
                          is_superuser=is_superuser,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given ,
        username and password.
        """
        return self._create_user(username, password, True, False,
                                 **extra_fields)

    def create_superuser(self, username=None, password=None, **extra_fields):
        """
        Creates and saves a Super User with the given ,
        username and password.
        """
        extra_fields['image'] = ''
        return self._create_user(username, password, True, True,
                                 **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(username__iexact=username)

    @classmethod
    def save_model(cls, obj):
        '''Save User'''
        obj.save()

#=========================================================================
# User Model
#=========================================================================

class ActiveManager(models.Manager):

    def get_queryset(self):
        queryset = super(ActiveManager, self).get_queryset()
        queryset = queryset.filter(is_active=True)
        return queryset


@python_2_unicode_compatible
class User(AbstractBaseUser, PermissionsMixin):
    """
    model for create user which extends AbstractBaseUser and Permissions
    """
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(
        max_length=80, unique=True, null=True)
    contact_number = models.CharField(max_length=50, null=True, blank=True,
                                      help_text="Please enter 10 digit number e.g. 9876543210")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False,
                                   help_text='Designates whether\
                                   the user can log into this admin site.')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    image = S3DirectField(dest='user_images',
                          help_text='Recommended image size is 300x300.',
                          null=True, blank=True)

    objects = CustomUserManager()
    active_users = ActiveManager()

    USERNAME_FIELD = 'username'

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta(object):
        '''User Meta Class'''
        verbose_name = 'User'
        verbose_name_plural = 'Users'

#=========================================================================
# Model for user address
#=========================================================================


@python_2_unicode_compatible
class UserAddress(TimeStamped):
    """
    model for User Addresses
    """
    address_line1 = models.CharField(max_length=100, blank=True, null=True)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    address_line3 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True,)
    state = models.ForeignKey(
        State, blank=True, null=True, related_name="state")
    country = models.ForeignKey(
        Country, default=1, db_index=False, related_name="country")
    post_code = models.CharField(max_length=50, blank=True, null=True)
    address_type = models.CharField(max_length=100,
                                    choices=AddressType.STATUS,
                                    default=AddressType.SENDER)

    def __str__(self):
        address = ''
        if self.address_line3:
            address = '%s, %s, %s, %s, %s, %s, %s' % (self.address_line1,
                                                      self.address_line2,
                                                      self.address_line3,
                                                      self.city,
                                                      self.state,
                                                      self.country,
                                                      self.post_code)
        if self.address_line1 and self.address_line2\
                and self.city and self.state \
                and self.country:
            address = '%s, %s, %s, %s, %s, %s' % (self.address_line1,
                                                  self.address_line2,
                                                  self.city,
                                                  self.state,
                                                  self.country,
                                                  self.post_code)
        return address


@python_2_unicode_compatible
class AlliancePartner(TimeStamped):
    """
    model for create user which extends AbstractBaseUser and Permissions
    """
    user = models.OneToOneField(User, blank=True, null=True)
    address = models.ForeignKey(UserAddress, blank=True, null=True)
    code = models.CharField(max_length=50, unique=True)
    stockist_margin = models.FloatField(
        _('Stockist Margin (in %)'), validators=[MinValueValidator(0), MaxValueValidator(99)], default='5')

    objects = models.Manager()
    
    active_ap = ActiveManager()

    class Meta(object):
        ''' meta details of AlliancePartner '''
        verbose_name = _('Alliance Partner')
        verbose_name_plural = _('Alliance Partners')

    def __str__(self):
        return self.user.name

    def thumbnail(self):
        '''return user thumbnail is user listing'''
        if self.user.image:
            return """<img border="0"
            alt="User Image" src="%s" height="50" />
            """ % (self.user.image)
        else:
            return 'Image Not Uploaded'

    thumbnail.allow_tags = True
    thumbnail.short_description = 'User Image'


@python_2_unicode_compatible
class RegionalDistributor(TimeStamped):
    '''
    model for create user which extends AbstractBaseUser and Permissions
    '''
    alliance_partner = models.ManyToManyField(
        AlliancePartner, related_name='alliance_distributor_related')
    user = models.OneToOneField(User, blank=True, null=True)
    address = models.ForeignKey(UserAddress, blank=True, null=True)
    code = models.CharField(max_length=50, unique=True)
    order_day = models.IntegerField(
        choices=OrderDay.STATUS, default=OrderDay.MONDAY)
    min_order = models.FloatField(verbose_name=mark_safe(u'Minimum Order (₹)'),
                                  validators=[MinValueValidator(1.0)])
    is_manual = models.BooleanField(_('Manual Order'), default=False)
    ap_dist_channel = models.CharField(
        _('Alliance Distribution Channel'), max_length=150, blank=True, null=True)
    ap_division = models.CharField(
        _('Alliance Division'), max_length=150, blank=True, null=True)
    ap_plant = models.CharField(
        _('Alliance Plant'), max_length=150, blank=True, null=True)

    objects = models.Manager()
    active_rs = ActiveManager()

    class Meta(object):
        ''' meta details of RegionalDistributor '''
        verbose_name = _('Redistribution Stockist')
        verbose_name_plural = _('Redistribution Stockists')

    def __str__(self):
        if self.user:
            return self.user.name
        else:
            return ''

    def thumbnail(self):
        ''' display thumbanil of uploaded image '''
        if self.user.image:
            return """<img border="0"
            alt="User Image" src="%s" height="50" />
            """ % (self.user.image)
        else:
            return 'Image Not Uploaded'

    thumbnail.allow_tags = True
    thumbnail.short_description = 'User Image'


@python_2_unicode_compatible
class RegionalSalesPromoter(TimeStamped):
    """
    model for create user which extends AbstractBaseUser and Permissions
    """
    regional_distributor = models.ForeignKey(RegionalDistributor,
                                             verbose_name='Redistribution Stockist')
    user = models.OneToOneField(User, blank=True, null=True,)
    address = models.ForeignKey(UserAddress, blank=True, null=True,)
    rsp_id = models.CharField(max_length=50, verbose_name='RSP ID')
    employee_number = models.CharField(max_length=50)

    objects = models.Manager()
    active_rsp = ActiveManager()

    class Meta(object):
        ''' meta details of RegionalSalesPromoter '''
        verbose_name = _('RSP')
        verbose_name_plural = _('RSPs')

    def __str__(self):
        return self.user.name

    def thumbnail(self):
        '''thubmnail'''
        if self.user.image:
            return """<img border="0"
            alt="User Image" src="%s" height="50" />
            """ % (self.user.image)
        else:
            return 'Image Not Uploaded'
    thumbnail.allow_tags = True
    thumbnail.short_description = 'User Image'


@python_2_unicode_compatible
class ShaktiEntrepreneur(TimeStamped):
    """
    model for create user which extends AbstractBaseUser and Permissions
    """
    regional_sales = models.ForeignKey(RegionalSalesPromoter,
                                       verbose_name='RSP',
                                       related_name='shakti_rsp')
    user = models.OneToOneField(User, blank=True, null=True,
                                related_name='shakti_user')
    address = models.ForeignKey(
        UserAddress, blank=True, null=True, related_name='shakti_address')
    code = models.CharField(max_length=50, unique=True)
    beat_name = models.CharField(max_length=100, blank=True, null=True)
    order_day = models.SmallIntegerField(
        choices=OrderDay.STATUS, default=OrderDay.MONDAY)
    min_order = models.FloatField(verbose_name=mark_safe(u'Minimum Order (₹)'),
                                  validators=[MinValueValidator(1.0)])

    objects = models.Manager()
    active_se = ActiveManager()

    class Meta(object):
        ''' meta details of ShaktiEntrepreneur '''
        verbose_name = _('Shakti Entrepreneur')
        verbose_name_plural = _('Shakti Entrepreneurs')

    def __str__(self):
        return "{0} : {1}".format(self.code, self.user.name)

    def thumbnail(self):
        '''Thumbnail'''
        if self.user.image:
            return """<img border="0"
            alt="User Image" src="%s" height="50" />
            """ % (self.user.image)
        else:
            return 'Image Not Uploaded'

    thumbnail.allow_tags = True
    thumbnail.short_description = 'User Image'


@python_2_unicode_compatible
class DistributorNorm(TimeStamped):
    '''
    model for product wise distributor norms
    '''
    from orders.models import Product

    distributor = models.ForeignKey(
        RegionalDistributor, related_name='distributor_norm')
    product = models.ForeignKey(Product, related_name='product_norm')
    norm = models.PositiveIntegerField(_('Norm (in cases)'))

    def __str__(self):
        return self.distributor.user.name

    class Meta(object):
        unique_together = ('distributor', 'product')


@python_2_unicode_compatible
class ForgotPassword(TimeStamped):
    '''
    Model for Forgot Password.
    '''
    user = models.ForeignKey(User)
    otp = models.IntegerField(db_index=True)
    token = models.CharField(max_length=50, null=True,
                             blank=True, db_index=True)
    otp_status_type = models.IntegerField(
        choices=OtpStatusType.STATUS,
        default=OtpStatusType.PENDING)
    expiration_date = models.DateTimeField()

    def __str__(self):
        return str(self.user.username)
