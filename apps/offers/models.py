# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, IntegrityError
from django.utils.translation import ugettext as _
from django.core.validators import MaxValueValidator, MinValueValidator, ValidationError
from django.core.exceptions import NON_FIELD_ERRORS
from django.utils import timezone

from hul.utility import TimeStamped
from app.models import RegionalSalesPromoter, ShaktiEntrepreneur, RegionalDistributor
from product.models import Product

MAX_DISCOUNT = 99


class DiscountType(object):
    PERCENT = 0
    QUANTITY = 1
    TRADE_OFFER = 2
    STATUS = (
        (PERCENT, 'Percentange'),
        (QUANTITY, 'Quantity'),
        (TRADE_OFFER, 'Quantity off for all'),
    )


class ShaktiBonusManager(models.Manager):

    def get_queryset(self):
        queryset = super(ShaktiBonusManager, self).get_queryset().filter(
            shakti_enterpreneur__isnull=False)
        return queryset


class ShaktiBonusAllManager(models.Manager):

    def get_queryset(self):
        queryset = super(ShaktiBonusAllManager, self).get_queryset().filter(
            shakti_enterpreneur__isnull=True)
        return queryset


class ShaktiPromotionManager(models.Manager):
    def get_queryset(self):
        return super(ShaktiPromotionManager, self).get_queryset().filter(
            discount_type=DiscountType.PERCENT)

    def create(self, **kwargs):
        kwargs.update({'discount_type': DiscountType.PERCENT})
        return super(ShaktiPromotionManager, self).create(**kwargs)


class ShaktiOfferManager(models.Manager):
    def get_queryset(self):
        return super(ShaktiOfferManager, self).get_queryset().filter(
            discount_type=DiscountType.QUANTITY)

    def create(self, **kwargs):
        kwargs.update({'discount_type': DiscountType.QUANTITY})
        return super(ShaktiOfferManager, self).create(**kwargs)


class TradeOfferManager(models.Manager):
    def get_queryset(self):
        return super(TradeOfferManager, self).get_queryset().filter(
            discount_type=DiscountType.TRADE_OFFER)

    def create(self, **kwargs):
        kwargs.update({'discount_type': DiscountType.TRADE_OFFER})
        return super(TradeOfferManager, self).create(**kwargs)


class Promotions(TimeStamped):
    name = models.CharField(max_length=100, unique=True)
    shakti_enterpreneur = models.ForeignKey(
        ShaktiEntrepreneur, to_field='user', null=True,
        related_name="%(app_label)s_%(class)s_related")
    discount_type = models.PositiveSmallIntegerField(
        choices=DiscountType.STATUS)
    start = models.DateField()
    end = models.DateField(_('Expires on'))

    class Meta(object):
        app_label = "offers"

    def clean(self, *args, **kwargs):
        super(Promotions, self).clean()
        errors = {}
        start_date = self.start
        end_date = self.end
        now = timezone.now().date()

        if start_date is not None and end_date is not None:
            if start_date < now:
                errors.update({'start': u'Start date cannot be of past'})

            if end_date < now:
                errors.update({'end': u'End date cannot be of past'})

            if end_date < start_date:
                errors.update(
                    {NON_FIELD_ERRORS: u"End date should be greater than start date."})

            if len(errors) > 0:
                raise ValidationError(errors)

    def __str__(self):
        return self.name


class PromotionLines(TimeStamped):
    promotion = models.ForeignKey(Promotions)
    buy_product = models.ForeignKey(
        Product, related_name="%(app_label)s_%(class)s_related")
    buy_quantity = models.PositiveIntegerField(_('Buy Quantity (in Units)'), validators=[
        MinValueValidator(1)
    ])
    free_product = models.ForeignKey(
        Product, related_name='free_product', blank=True, null=True)
    free_quantity = models.PositiveIntegerField(blank=True, null=True)
    discount = models.PositiveIntegerField(_('Discount (%)'), validators=[
        MaxValueValidator(MAX_DISCOUNT),
        MinValueValidator(1)],
        blank=True, null=True)

    class Meta(object):
        app_label = "offers"

    def __str__(self):
        return self.promotion.name


class ShaktiBonus(TimeStamped):
    objects = ShaktiBonusManager()

    shakti_enterpreneur = models.OneToOneField(
        ShaktiEntrepreneur, to_field='user', blank=True, null=True)
    start = models.DateField()
    end = models.DateField(_('Expires on'))

    class Meta(object):
        app_label = "offers"
        verbose_name_plural = 'Shakti Bonus'

    def __init__(self, *args, **kwargs):
        super(ShaktiBonus, self).__init__(*args, **kwargs)
        self.initial_start = self.start
        self.initial_end = self.end

    def clean(self, *args, **kwargs):
        super(ShaktiBonus, self).clean()
        errors = {}
        start_date = self.start
        end_date = self.end
        now = timezone.now().date()

        if start_date is not None and end_date is not None:
            if start_date < now and self.initial_start is None:
                errors.update({'start': u'Start date cannot be of past'})

            if end_date < now and self.initial_end is None:
                errors.update({'end': u'End date cannot be of past'})

            if end_date < start_date:
                errors.update(
                    {NON_FIELD_ERRORS: u"End date should be greater than start date."})

            if len(errors) > 0:
                raise ValidationError(errors)

    def __str__(self):
        return "{0}".format(self.shakti_enterpreneur)


class ShaktiBonusLines(TimeStamped):
    PERCENT = 1
    CASH = 2
    choices = (
        (PERCENT, 'Percentage'),
        (CASH, 'Cash'),
    )
    shakti_bonus = models.ForeignKey(ShaktiBonus)
    target_amount = models.PositiveIntegerField()
    discount_type = models.SmallIntegerField(choices=choices, default=PERCENT)
    discount = models.PositiveIntegerField(_('Discount'))

    class Meta(object):
        app_label = "offers"
        verbose_name_plural = _('Shakti Bonus Lines')
        verbose_name = _('Shakti Bonus Lines')
        unique_together = ('shakti_bonus', 'target_amount')

    def clean(self, *args, **kwargs):
        super(ShaktiBonusLines, self).clean()
        errors = {}

        if self.discount_type == self.PERCENT and self.discount > 99:
            errors.update(
                {'discount': u'Ensure this value is less than or equal to 99.'})

        if (self.discount_type == self.PERCENT or self.discount_type == self.CASH) and self.discount < 0:
            errors.update(
                {'discount': u'Ensure this value is greater than or equal to 1.'})

        if self.discount_type == self.CASH and self.discount > 9999:
            errors.update(
                {'discount': u'Ensure this value is less than or equal to 9999.'})

        if len(errors) > 0:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.pk:
            try:
                p = ShaktiBonusLines.objects.get(
                    shakti_bonus=self.shakti_bonus, target_amount=self.target_amount)
                self.created = timezone.now()
                self.pk = p.pk
            except IntegrityError:
                pass
            except ShaktiBonusLines.DoesNotExist:
                pass

        super(ShaktiBonusLines, self).save(*args, **kwargs)

    def __str__(self):
        return "{0}".format(self.shakti_bonus.shakti_enterpreneur)


class ShaktiBonusAll(ShaktiBonus):
    objects = ShaktiBonusAllManager()

    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Bonus to All')

    def __str__(self):
        return "{0}".format(self.id)


class ShaktiBonusAllLines(ShaktiBonusLines):
    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Bonus to All Lines')


class ShaktiPromotions(Promotions):
    objects = ShaktiPromotionManager()

    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Shakti Promotions')

    def save(self, *args, **kwargs):
        if self.discount_type is None:
            self.discount_type = DiscountType.PERCENT
        super(ShaktiPromotions, self).save(*args, **kwargs)


class ShaktiPromotionLines(PromotionLines):
    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Shakti Promotion Lines')

    def clean(self, *args, **kwargs):
        super(ShaktiPromotionLines, self).clean(*args, **kwargs)
        if self.discount is None:
            raise ValidationError({
                'discount': ['This field is required', ],
            })


class ShaktiOffers(Promotions):
    objects = ShaktiOfferManager()

    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Shakti Offers')
        verbose_name = _('Shakti Offers')

    def save(self, *args, **kwargs):
        if self.discount_type is None:
            self.discount_type = DiscountType.QUANTITY
        super(ShaktiOffers, self).save(*args, **kwargs)


class ShaktiOffersLines(PromotionLines):
    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Shakti offer Lines')

    def clean(self, *args, **kwargs):
        super(ShaktiOffersLines, self).clean(*args, **kwargs)
        errors = {}
        if self.free_product is None:
            errors.update({
                'free_product': ['This field is required'],
            })

        if self.free_quantity is None:
            errors.update({
                'free_quantity': ['This field is required'],
            })

        if len(errors) > 0:
            raise ValidationError(errors)


class TradeOffers(Promotions):
    objects = TradeOfferManager()

    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Trade Offers')
        verbose_name = _('Trade Offers')

    def save(self, *args, **kwargs):
        if self.discount_type is None:
            self.discount_type = DiscountType.TRADE_OFFER
        super(TradeOffers, self).save(*args, **kwargs)


class TradeOffersLines(PromotionLines):
    class Meta(object):
        app_label = "offers"
        proxy = True
        verbose_name_plural = _('Trade offers Lines')

    def clean(self, *args, **kwargs):
        super(TradeOffersLines, self).clean(*args, **kwargs)
        errors = {}
        if self.discount is None:
            errors.update({
                'discount': ['This field is required', ],
            })

        if len(errors) > 0:
            raise ValidationError(errors)


class DiscountToShakti(TimeStamped):
    '''
    Discount to Shakti, defined by Distributor
    '''
    name = models.CharField(max_length=255, blank=True)
    regional_distributor = models.OneToOneField(
        RegionalDistributor, to_field="user_id", related_name="distributoroffers")
    start = models.DateField()
    end = models.DateField()
    discount_type = models.PositiveSmallIntegerField(
        choices=ShaktiBonusAllLines.choices, default=ShaktiBonusLines.PERCENT)
    discount = models.PositiveIntegerField()

    class Meta(object):
        app_label = "offers"
        db_table = "{app_label}_shaktidiscount".format(app_label=app_label)
        verbose_name_plural = "Discount to Shakti"
        verbose_name = "Discount to Shakti"

    def __str__(self):
        return "{0}".format(self.name)

    def clean(self, *args, **kwargs):
        super(DiscountToShakti, self).clean(*args, **kwargs)
        errors = {}

        if self.discount_type == ShaktiBonusLines.PERCENT and self.discount > 99:
            errors.update(
                {'discount': u'Ensure this value is less than or equal to 99.'})

        if (self.discount_type == ShaktiBonusLines.PERCENT or self.discount_type == ShaktiBonusLines.CASH) and self.discount < 0:
            errors.update(
                {'discount': u'Ensure this value is greater than or equal to 1.'})

        if self.discount_type == ShaktiBonusLines.CASH and self.discount > 9999:
            errors.update(
                {'discount': u'Ensure this value is less than or equal to 9999.'})
        
        if self.start > self.end:
            errors.update({
                'start': u'Start date should be less than discount end date.'
            })

        if len(errors) > 0:
            raise ValidationError(errors)


