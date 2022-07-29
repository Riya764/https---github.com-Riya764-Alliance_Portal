# -*- coding: utf-8 -*-
'''order models'''
from __future__ import unicode_literals

from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.db import models, models
from django.db.models import Sum
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.contrib.postgres.fields import JSONField

from hul.choices import OrderStatus, PaymentStatus, CancelOrderReasons, ClaimStatus
from hul.utility import TimeStamped

from app.models import (User, UserAddress, ShaktiEntrepreneur,
                        AlliancePartner, RegionalDistributor, RegionalSalesPromoter)
from moc.models import MoCMonth
from product.models import Product
from offers.models import ShaktiBonusLines, DiscountToShakti
from django.db.models import Q
from datetime import datetime as dt


@python_2_unicode_compatible
class DistributorOrder(TimeStamped):
    ''' orders of Distributors places by Sales Promotor '''
    distributor = models.ForeignKey(User,
                                    related_name='do_distributor_related',
                                    verbose_name='Redistribution Stockist')
    sales_promoter = models.ForeignKey(User,
                                       blank=True, null=True,
                                       related_name='do_salespromoter_related',
                                       verbose_name='RSP')
    shakti_enterpreneur = models.ForeignKey(User,
                                            related_name='do_shaktientrepreneur_related')
    shipping_address = models.ForeignKey(UserAddress, null=True, blank=True)
    order_status = models.IntegerField(choices=OrderStatus.STATUS,
                                       default=OrderStatus.ORDERED)
    payment_status = models.IntegerField(choices=PaymentStatus.STATUS,
                                         default=PaymentStatus.PENDING)
    amount = models.FloatField(verbose_name=mark_safe(u"Gross Amount (₹)"))
    tax = models.FloatField(verbose_name=mark_safe(u"Tax (₹)"), default=0)
    discount_amount = models.FloatField(
        verbose_name=mark_safe(u"Discount Amount (₹)"), default=0)
    promotion = ArrayField(models.IntegerField(
        null=True, blank=True), null=True, blank=True)
    total_amount = models.FloatField(
        verbose_name=mark_safe(u"Total Amount (₹)"))
    invoice_number = models.CharField(max_length=50, null=True, blank=True)
    cancel_order = models.IntegerField('Reason for cancellation',
                                       choices=CancelOrderReasons.STATUS,
                                       null=True, blank=True)
    cancel_reason = models.CharField(
        'Enter your reason', max_length=255, null=True, blank=True)
    dispatched_on = models.DateTimeField(
        'Dispatched On', null=True, blank=True)
    moc = models.ForeignKey(
        MoCMonth, related_name='secondary_order_moc', blank=True, null=True)
    cgst_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"CGST Total (?)"), null=True)
    sgst_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"SGST Total (?)"), null=True)
    igst_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"IGST Total (?)"), null=True)

    class Meta:
        ''' meta details of DistributorOrder '''
        verbose_name = _('Secondary Order')
        verbose_name_plural = _('Secondary Orders')

    def __str__(self):
        return 'RSP%s' % str(self.pk).zfill(6)

    def get_moc_name(self):
        if self.moc is not None:
            return "{0}-{1}".format(self.moc.name, self.moc.moc_year.year)
        return "{0}".format('-')

    def get_total_quantity(self):
        order_quantity = self.distributor_order_details.\
            values_list('dispatch_quantity').aggregate(
                total_quantity=Sum('dispatch_quantity'))
        return order_quantity['total_quantity'] or 0

    def save(self, *args, **kwargs):
        '''
        overriding save method to update dispatch datetime
        '''
        if self.order_status == OrderStatus.DISPATCHED:
            self.dispatched_on = timezone.now()
            if self.total_amount == 0:
                self.order_status = OrderStatus.CANCELLED
            curr_year = dt.now().year
            curr_month = dt.now().month
            start_date = ""
            end_date = ""
            if curr_month > 3:
                start_date = str(curr_year) + "-04-01"
                end_date = str(curr_year + 1) + "-04-01"
            else:
                start_date = str(curr_year - 1) + "-04-01"
                end_date = str(curr_year) + "-04-01"
            order = DistributorOrder.objects.filter(
                distributor_id=self.distributor_id).filter(
                    Q(order_status=OrderStatus.DISPATCHED) | Q(order_status=OrderStatus.RETURNED)).filter(
                        dispatched_on__range=[start_date, end_date]).count()

            order = DistributorOrder.objects.filter(
                distributor_id=self.distributor_id).filter(
                    Q(order_status=OrderStatus.DISPATCHED) | Q(order_status=OrderStatus.RETURNED)).filter(
                        dispatched_on__range=[start_date, end_date]).count()

            code = RegionalDistributor.objects.filter(
                user=self.distributor_id).values("code").first()["code"]
            self.invoice_number = '%s/%s/%s' % (str(code),
                                                str(curr_year), str(order).zfill(6))
        super(DistributorOrder, self).save(*args, **kwargs)


@python_2_unicode_compatible
class DistributorOrderDetail(TimeStamped):
    ''' distributor order details of DistributorOrder'''
    distributor_order = models.ForeignKey(DistributorOrder,
                                          related_name='distributor_order_details', null=True, blank=True)
    shipping_address = models.ForeignKey(
        UserAddress, null=True, blank=True, related_name="do_shipping")
    product = models.ForeignKey(Product, related_name="distributororderdetail")
    quantity = models.IntegerField()
    dispatch_quantity = models.IntegerField(null=True, blank=True)
    unitprice = models.FloatField(verbose_name=mark_safe(
        u"Base Rate (₹)"),  help_text='base rate + stockist margin')
    price = models.FloatField(verbose_name=mark_safe(u"Price (₹)"),
                              help_text='Base price * quantity')
    net_amount = models.FloatField(verbose_name=mark_safe(u"Net Amount (₹)"),
                                   help_text='taxable amount + taxes')
    promotion = ArrayField(models.IntegerField(
        null=True, blank=True), blank=True)
    promotion_applied = models.CharField(max_length=255,
                                         null=True, blank=True)
    discount_amount = models.FloatField(verbose_name=mark_safe(
        u"Discount Amount (₹)"), blank=True, null=True)
    distributor_promotion = models.ForeignKey(
        DiscountToShakti, on_delete=models.SET_NULL, blank=True, null=True)
    distributor_discount = models.FloatField(verbose_name=mark_safe(u"Discount to Shakti (₹)"),
                                             help_text='Scheme Discount by Stockist', default=0)
    distributor_discount_percent = models.FloatField(verbose_name=mark_safe(u"Discount to Shakti (₹%)"),
                                                     help_text='Scheme Discount in Percentage by Stockist', default=0)
    cgst = models.FloatField(verbose_name=mark_safe(
        u"CGST (₹)"), default=0)
    sgst = models.FloatField(verbose_name=mark_safe(
        u"SGST (₹)"), default=0)
    igst = models.FloatField(verbose_name=mark_safe(
        u"IGST (₹)"), default=0)
    is_free = models.BooleanField(default=False)
    is_cld = models.BooleanField(default=False)
    item_status = models.IntegerField(choices=OrderStatus.STATUS,
                                      default=OrderStatus.ORDERED)
    dispatched_on = models.DateTimeField(
        'Dispatched On', null=True, blank=True)
    product_info = JSONField(blank=True, null=True)

    returned_units=models.IntegerField(null=True,blank=True,default=0)

    class Meta:
        ''' meta details of DistributorOrderDetail '''
        verbose_name = _('Secondary Order Detail')
        verbose_name_plural = _('Secondary Order Details')

    def __str__(self):
        return str(self.product)

    def save(self, *args, **kwargs):
        '''
        overriding save method to update dispatch datetime
        '''
        if self.item_status == OrderStatus.DISPATCHED:
            if self.net_amount == 0:
                self.item_status = OrderStatus.CANCELLED
            self.dispatched_on = timezone.now()
        super(DistributorOrderDetail, self).save(*args, **kwargs)

    def get_units(self):
        units = divmod(self.quantity, self.product.cld_configurations)
        return units[1]
    get_units.short_description = 'Ordered Units'

    def get_cases(self):
        units = divmod(self.quantity, self.product.cld_configurations)
        return units[0]
    get_cases.short_description = 'Ordered Cases'

    def get_dispatch_units(self):
        if self.dispatch_quantity is not None:
            units = divmod(self.dispatch_quantity,
                           self.product.cld_configurations)
            return units[1]
        else:
            return '-'
    get_dispatch_units.short_description = 'Dispatch Units'

    def get_dispatch_cases(self):

        if self.dispatch_quantity is not None:
            units = divmod(self.dispatch_quantity,
                           self.product.cld_configurations)
            return units[0]
        else:
            return '-'
    get_dispatch_cases.short_description = 'Dispatch Cases'

    def get_hsn_code(self):
        return self.product.hsn_code
    get_hsn_code.short_description = 'HSN Code'


@python_2_unicode_compatible
class ReviewPrimaryOrder(TimeStamped):
    ''' orders of Alliances placed by Distributor '''
    distributor = models.ForeignKey(User, related_name="rpo_distributoruser", null=True,
                                    blank=True, verbose_name='Redistribution Stockist')
    shipping_address = models.ForeignKey(UserAddress)
    amount = models.FloatField(
        verbose_name=mark_safe(u"Order Amount (₹)"), default=0)
    tax = models.FloatField(verbose_name=mark_safe(
        u"Tax (₹)"), default=0)
    discount_amount = models.FloatField(
        verbose_name=mark_safe(u"Discount Amount (₹)"), default=0)
    promo_code = models.CharField(max_length=55, null=True, blank=True)
    total_amount = models.FloatField(
        verbose_name=mark_safe(u"Total Amount (₹)"))
    is_placed = models.BooleanField(default=False)
    is_discarded = models.BooleanField(default=False)

    class Meta:
        ''' meta details of DistributorOrder '''
        verbose_name = _('Primary Order Page')
        verbose_name_plural = _('Primary Orders Page')

    def __str__(self):
        return str(self.id)


@python_2_unicode_compatible
class ReviewPrimaryOrderDetail(TimeStamped):
    ''' Alliance order details of AllianceOrder'''
    review_primary_order = models.ForeignKey(
        ReviewPrimaryOrder, null=True, blank=True)
    alliance = models.ForeignKey(User, related_name="rpo_allianceuser",
                                 null=True, blank=True)
    alliance_code = models.CharField(max_length=20, null=True, blank=True)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(_('Quantity (in cases)'))
    order_generated = models.IntegerField(_('Order Generated (in cases)'))
    unitprice = models.FloatField(verbose_name=mark_safe(u"Base Price (₹)"),
                                  help_text="base price from Products table")
    price = models.FloatField(verbose_name=mark_safe(
        u"Price (₹)"), help_text="base price * quantity")
    cgst_amount = models.FloatField(
        verbose_name=mark_safe(u"CGST Amount (₹)"), default=0)
    sgst_amount = models.FloatField(
        verbose_name=mark_safe(u"SGST Amount (₹)"), default=0)
    igst_amount = models.FloatField(
        verbose_name=mark_safe(u"IGST Amount (₹)"), default=0)

    class Meta:
        ''' meta details of DistributorOrderDetail '''
        verbose_name = _('Order Detail')
        verbose_name_plural = _('Order Details')

    def __str__(self):
        return ''

    def set_units(self):
        ''' convert ordered quantity to units '''
        units = self.quantity * self.product.cld_configurations
        return units

    def get_cases(self):
        ''' convert ordered quantity to cases '''
        units = divmod(self.quantity, self.product.cld_configurations)
        return units[0]
    get_cases.short_description = 'Cases'

    def get_basepack_code(self):
        return self.product.basepack_code
    get_basepack_code.short_description = 'Basepack Code'

    def get_cld(self):
        return self.product.cld_configurations
    get_cld.short_description = 'CLD configuration'

    def get_norm(self):
        regionaldistributor = self.review_primary_order.distributor.regionaldistributor
        product_norm = self.product.product_norm.filter(
            distributor=regionaldistributor).first()
        return product_norm.norm if product_norm else ""
    get_norm.short_description = 'Norm'

    def get_stock_inhand(self):
        distributor = self.review_primary_order.distributor
        closing_stock = self.product.distributorstock.filter(
            distributor=distributor).order_by('-id').first().closing_stock
        return closing_stock
    get_stock_inhand.short_description = 'Stock in Hand'

    def get_stock_inhand_price(self):
        from orders.lib.order_management import CalculatePrice
        closing_stock = self.get_stock_inhand()
        taxable_amount = self.unitprice * closing_stock
        taxes = {'cgst': self.product.cgst,
                 'sgst': self.product.sgst, 'igst': self.product.igst}
        value = CalculatePrice().calculate_tax(taxable_amount, **taxes)[0]

        return value
    get_stock_inhand_price.short_description = "Stock in Hand Value (₹)"

    def get_stock_intransit(self):
        distributor = self.review_primary_order.distributor
        transit_stock = self.product.alliancepartnerorderdetail.filter(
            item_status=OrderStatus.INTRANSIT,
            alliance_partner_order__distributor=distributor).aggregate(
            total_quantity=Sum('dispatch_quantity'))
        return transit_stock['total_quantity'] or 0
    get_stock_intransit.short_description = 'Stock in Transit'

    def get_stock_intransit_price(self):
        ''' return value of inhand stock '''
        from orders.lib.order_management import CalculatePrice
        quantity = self.get_stock_intransit()
        taxable_amount = self.unitprice * quantity
        taxes = {'cgst': self.product.cgst,
                 'sgst': self.product.sgst, 'igst': self.product.igst}
        value = CalculatePrice().calculate_tax(taxable_amount, **taxes)[0]
        return value

    get_stock_intransit_price.short_description = "Stock in Transit Value (₹)"

    def clean(self):
        self.order_generated = round(self.order_generated)
        if self.order_generated < self.quantity:
            pass
            # raise ValidationError(
            #     _('Order Quantity cannot be less than: %(value)s'),
            #     params={'value': self.quantity},
            # )

        distributor_id = self.review_primary_order.distributor.regionaldistributor.id
        product_norm = self.product.product_norm.filter(
            distributor=distributor_id).first().norm
        upper_limit = 10 * product_norm

        if self.order_generated > upper_limit and product_norm > 0:
            raise ValidationError(
                _('Order Quantity cannot be greater than: %(value)s'),
                params={'value': upper_limit},
            )


@python_2_unicode_compatible
class AlliancePartnerOrder(TimeStamped):
    ''' orders of Alliances placed by Distributor '''
    alliance = models.ForeignKey(User, related_name="apo_allianceuser_related",
                                 null=True, blank=True)
    review_primary_order = models.ForeignKey(
        ReviewPrimaryOrder, related_name="apo_review_primary", null=True, blank=True)
    distributor = models.ForeignKey(User, related_name="apo_distributoruser_related", null=True,
                                    blank=True, verbose_name='Redistribution Stockist')
    distributor_name = models.CharField(max_length=150, null=True, blank=True)
    alliance_code = models.CharField(max_length=20, null=True, blank=True)
    shipping_address = models.ForeignKey(UserAddress)
    order_status = models.IntegerField(choices=OrderStatus.APSTATUS,
                                       default=OrderStatus.ORDERED)
    payment_status = models.IntegerField(choices=PaymentStatus.STATUS,
                                         default=PaymentStatus.PENDING)
    amount = models.FloatField(verbose_name=mark_safe(u"Gross Amount (₹)"))

    tax = models.FloatField(verbose_name=mark_safe(u"Tax Amount"), default=0)

    discount_amount = models.FloatField(
        verbose_name=mark_safe(u"Discount Amount (₹)"), default=0)
    promo_code = models.CharField(max_length=55, null=True, blank=True)
    total_amount = models.FloatField(
        verbose_name=mark_safe(u"Total Amount (₹)"))
    invoice_number = models.CharField(max_length=50, null=True, blank=True)
    invoice_number_alliance = models.CharField(
        max_length=500, null=True, blank=True, help_text="This is received from Alliance csv")
    order_id = models.IntegerField(_('Order ID'), null=True)
    cancel_order = models.IntegerField('Reason for cancellation', choices=CancelOrderReasons.STATUS,
                                       null=True, blank=True)
    cancel_reason = models.CharField(
        'Enter your reason', max_length=255, null=True, blank=True)
    dispatched_on = models.DateTimeField(
        'Dispatched On', null=True, blank=True)
    has_claim = models.BooleanField(default=False)
    claim_status = models.IntegerField(
        choices=ClaimStatus.STATUS, default=ClaimStatus.NONE)
    moc = models.ForeignKey(
        MoCMonth, related_name='primary_order_moc', blank=True, null=True)
    cgst_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"CGST Total (?)"))

    sgst_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"SGST Total (?)"))

    dis_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"Discount Total (?)"))

    sta_total = models.FloatField(
        default=0, verbose_name=mark_safe(u"Stales Disc Total (?)"))

    class Meta:
        ''' meta details of DistributorOrder '''
        verbose_name = _('Primary Order')
        verbose_name_plural = _('Primary Orders')
        unique_together = ('distributor', 'order_id')

    def __str__(self):
        return self.invoice_number

    def get_moc_name(self):
        if self.moc is not None:
            return "{0}-{1}".format(self.moc.name, self.moc.moc_year.year)
        return "{0}".format('-')

    def save(self, *args, **kwargs):
        '''
        overriding save method to update dispatch datetime
        '''
        if self.order_status == OrderStatus.DISPATCHED:
            self.dispatched_on = timezone.now()
        super(AlliancePartnerOrder, self).save(*args, **kwargs)


@python_2_unicode_compatible
class AlliancePartnerOrderDetail(TimeStamped):
    ''' Alliance order details of AllianceOrder'''
    alliance_partner_order = models.ForeignKey(AlliancePartnerOrder)
    product = models.ForeignKey(
        Product, related_name="alliancepartnerorderdetail")
    product_name = models.CharField(max_length=150, null=True, blank=True)
    quantity = models.IntegerField()
    dispatch_quantity = models.IntegerField(null=True, blank=True)
    unitprice = models.FloatField(verbose_name=mark_safe(u"Base Price (₹)"),
                                  help_text="base price from Products table")
    cgst_amount = models.FloatField(
        verbose_name=mark_safe(u"CGST Amount (₹)"), default=0)
    sgst_amount = models.FloatField(
        verbose_name=mark_safe(u"SGST Amount (₹)"), default=0)
    igst_amount = models.FloatField(
        verbose_name=mark_safe(u"IGST Amount (₹)"), default=0)
    cess_amount = models.FloatField(
        verbose_name=mark_safe(u"Cess Amount (₹)"), default=0)
    cgst = models.FloatField(verbose_name=mark_safe(u"CGST (%)"), default=0)
    sgst = models.FloatField(verbose_name=mark_safe(u"SGST (%)"), default=0)
    igst = models.FloatField(verbose_name=mark_safe(u"IGST (%)"), default=0)
    cess = models.FloatField(verbose_name=mark_safe(u"Cess (%)"), default=0)
    prd_discount = models.FloatField(
        default=0, help_text="This value is discount given in products")
    add_discount = models.FloatField(
        default=0, help_text="Additional discount given for customer")
    sch_discount = models.FloatField(default=0, help_text="Scheme Discount")
    asch_discount = models.FloatField(
        default=0, help_text="Additional scheme discount")
    disp_discount = models.FloatField(
        default=0, help_text="Disposable item discount")
    trade_discount = models.FloatField(default=0, help_text="Trade Discount")
    cash_discount = models.FloatField(default=0, help_text="Cash Discount")
    discount_amount = models.FloatField(
        verbose_name=mark_safe(u"Discount (₹)"), default=0)
    price = models.FloatField(verbose_name=mark_safe(u"Price (₹)"))
    item_status = models.IntegerField(choices=OrderStatus.APSTATUS,
                                      default=OrderStatus.ORDERED)
    dispatched_on = models.DateTimeField(
        'Dispatched On', null=True, blank=True)
    batch_code = models.CharField(max_length=150, null=True, blank=True)
    prod_date = models.DateTimeField(null=True, blank=True)
    base_price_par_unit = models.FloatField(
        default=0, verbose_name=mark_safe(u"Base Price Per Unit (?)"))
    total_amt_base_peice = models.FloatField(
        default=0, verbose_name=mark_safe(u"Total Amt (Base price) (?)"))
    invoice_number_alliance = models.CharField(
        max_length=100, null=True, blank=True)

    class Meta:
        ''' meta details of DistributorOrderDetail '''
        verbose_name = _('Primary Order Detail')
        verbose_name_plural = _('Primary Order Details')

    def __str__(self):
        return ''

    def save(self, *args, **kwargs):
        '''
        overriding save method to update dispatch datetime
        '''
        if self.item_status == OrderStatus.DISPATCHED:
            self.dispatched_on = timezone.now()
        super(AlliancePartnerOrderDetail, self).save(*args, **kwargs)

    def get_units(self):
        ''' convert ordered quantity to units '''
        units = divmod(self.quantity, self.product.cld_configurations)
        return units[1]
    get_units.short_description = 'Ordered Units'

    def get_cases(self):
        ''' convert ordered quantity to cases '''
        units = divmod(self.quantity, self.product.cld_configurations)
        return units[0]
    get_cases.short_description = 'Ordered Cases'

    def get_dispatch_units(self):
        ''' convert quantity to units '''
        if self.dispatch_quantity is not None:
            units = divmod(self.dispatch_quantity,
                           self.product.cld_configurations)
            return units[1]
        else:
            return '-'
    get_dispatch_units.short_description = 'Dispatched Units'

    def get_dispatch_cases(self):
        ''' convert quantity to cases '''
        if self.dispatch_quantity is not None:
            units = divmod(self.dispatch_quantity,
                           self.product.cld_configurations)
            return units[0]
        else:
            return '-'
    get_dispatch_cases.short_description = 'Dispatched Cases'


@python_2_unicode_compatible
class AlliancePartnerDiscountDetail(TimeStamped):
    ''' Alliance order details of AllianceOrder'''
    alliance_partner_order = models.ForeignKey(AlliancePartnerOrder)
    product = models.ForeignKey(
        Product, related_name="alliancepartnerdiscountdetail")
    product_name = models.CharField(max_length=150, null=True, blank=True)
    total_quantity = models.IntegerField()
    discount_amount = models.FloatField(
        verbose_name=mark_safe(u"Discount Amount (₹)"))

    class Meta:
        ''' meta details of allianceOrderDiscountDetail '''
        verbose_name = _('Primary Order Discount Detail')
        verbose_name_plural = _('Primary Order Discount Details')

    def __str__(self):
        return ''


@python_2_unicode_compatible
class AlliancePartnerShaktiDiscount(TimeStamped):
    ''' Shakti Bonus details of AllianceOrder'''
    alliance_partner_order = models.ForeignKey(AlliancePartnerOrder)
    shakti_enterpreneur = models.ForeignKey(
        ShaktiEntrepreneur, to_field='user', blank=True, null=True)
    shakti_bonus_line = models.ForeignKey(
        ShaktiBonusLines, blank=True, null=True)
    discount_amount = models.FloatField(
        verbose_name=mark_safe(u"Discount Amount (₹)"))

    class Meta:
        ''' meta details of allianceOrderDiscountDetail '''
        verbose_name = _('Primary Order Shakti Discount Detail')
        verbose_name_plural = _('Primary Order Shakti Discount Details')

    def __str__(self):
        return ''


@python_2_unicode_compatible
class DistributorStock(models.Model):
    ''' distributor opening closing stocks '''
    product = models.ForeignKey(Product, related_name="distributorstock")
    distributor = models.ForeignKey(User)
    opening_stock = models.IntegerField(default=0)
    closing_stock = models.IntegerField(default=0)
    amount = models.FloatField(
        verbose_name=mark_safe(u"Amount (₹)"), default=0)
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.pk)

    # def get_units(self):
    #     ''' convert ordered quantity to units '''
    #     units = divmod(self.closing_stock, self.product.cld_configurations)
    #     return units[1]
    # get_units.short_description = 'Closing Units'

    # def get_cases(self):
    #     ''' convert ordered quantity to cases '''
    #     units = divmod(self.closing_stock, self.product.cld_configurations)
    #     return units[0]
    # get_cases.short_description = 'Closing Cases'

    def get_distributor_code(self):
        return self.distributor.regionaldistributor.code
    get_distributor_code.short_description = 'Distributor Code'

    def get_basepack_code(self):
        return self.product.basepack_code
    get_basepack_code.short_description = 'Basepack Code'


class AlliancePartnerDistributorOrder(AlliancePartnerOrderDetail):
    ''' Displays quantity ordered by RS '''
    class Meta:
        proxy = True
        verbose_name_plural = 'Other Primary Order Details'
