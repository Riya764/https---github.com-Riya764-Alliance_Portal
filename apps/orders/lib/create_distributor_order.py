''' orders/lib/create_distributor_order.py '''
from __future__ import division
import logging
import json
from django.conf import settings
from django.utils import timezone as dt
from django.db import transaction
from django.core.mail import EmailMessage
from django.db.models import Sum, Count, Q, F

from hul.choices import OrderStatus, ClaimStatus

from app.models import RegionalDistributor, DistributorNorm
from orders.models import (AlliancePartnerOrder, AlliancePartnerOrderDetail,
                           DistributorOrderDetail,
                           AlliancePartnerDiscountDetail,
                           DistributorStock, ReviewPrimaryOrder,
                           ReviewPrimaryOrderDetail, AlliancePartnerShaktiDiscount)
from orders.stock_management import StockManagement
from orders.lib.order_management import CalculatePrice, OrderManagement
from orders.lib.order_files import GenerateFile
from offers.models import ShaktiBonusLines
from product.models import Product

logger = logging.getLogger(__name__)
'''
get distributors for current day or is_automatic is false
create their order according to stock in hand logic
order will be placed to alliance at 9 pm
after placing order make is_automatic to true
'''


class CreateReviewOrder(object):
    distributors = []
    now = ''
    today = ''
    tomorrow = ''
    yesterday = ''
    review_order_details = {}

    SQL = '''
        select rd.id, rd.user_id, rd.address_id , norm.product_id, norm.norm, SUM(apd.dispatch_quantity) as stock_intransit, ds.closing_stock, ds.product_id,
        p.partner_code, p.basepack_name as product_name, p.cld_configurations, alliance.user_id as brand_id, p.base_rate, p.cgst, p.sgst, p.igst
        from app_regionaldistributor as rd
        inner join app_distributornorm as norm on norm.distributor_id = rd.id
        inner join orders_distributorstock as ds on ds.distributor_id = rd.user_id and norm.product_id = ds.product_id and ds.modified > CURRENT_DATE - interval '1 day'
        left join product_product as p on norm.product_id = p.id
        left join app_alliancepartner as alliance on alliance.id = p.brand_id
        left join orders_alliancepartnerorder as apo on rd.user_id = apo.distributor_id
        left join orders_alliancepartnerorderdetail as apd on apd.alliance_partner_order_id = apo.id and apd.product_id = norm.product_id and apd.item_status = %s
        group by p.id, norm.product_id, rd.user_id, rd.id, ds.id, norm.id, alliance.user_id
        having (rd.is_manual = true or rd.order_day = %s) and p.is_active = true and rd.is_active = true order by ds.created desc;

        '''

    def __init__(self):
        self.now = dt.now()
        self.today = self.now.replace(
            hour=0, minute=0, second=0, microsecond=0)
        self.tomorrow = self.today + dt.timedelta(days=1)
        self.yesterday = self.today - dt.timedelta(days=1)
        self.review_order_details = {}
        self.distributors = self._get_distributors()

    def _get_distributors(self):
        '''
        get all distributors for current order day and is automatic is false
        '''
        today = self.now.isoweekday()
        if today == 7:
            day = 1
        else:
            day = today + 1

        distributors = RegionalDistributor.objects.raw(
            self.SQL, [OrderStatus.INTRANSIT, day])

        return distributors

    def generate_order(self):
        '''
        get closing stock(distributor stock), stock in transit(Aliiancepartnerorder), stock norms(distributor norms),
        calculate stock with which order to be generated
        '''

        self._set_distributor_order(self.distributors)
        if self.review_order_details:
            self._save_review_orders()

    def _set_distributor_order(self, distributors):

        for distributor in distributors:
            distributor_id = distributor.user_id
            product_id = distributor.product_id

            closing_stock = distributor.closing_stock or 0
            intransit_stock = distributor.stock_intransit or 0

            quantity = self._calculate_available_stock(
                closing_stock, intransit_stock, distributor.norm, distributor.cld_configurations)

            if distributor_id not in self.review_order_details:

                self.review_order_details[distributor_id] = {}
                order = {}
                order['distributor'] = distributor_id
                order['shipping_address'] = distributor.address_id
                order['amount'] = 0
                order['tax'] = 0
                order['total_amount'] = 0
                order['orderlines'] = []
                self.review_order_details[distributor_id] = order

            orderlines = {}

            orderlines['alliance_code'] = distributor.partner_code
            orderlines['alliance_id'] = distributor.brand_id
            orderlines['product_id'] = product_id

            if quantity < distributor.norm or quantity == 0:
                orderlines['quantity'] = abs(quantity)
                orderlines['order_generated'] = abs(quantity)
            else:
                orderlines['quantity'] = 0
                orderlines['order_generated'] = 0

            orderlines['unitprice'] = distributor.base_rate
            subtotal = orderlines['unitprice'] * \
                orderlines['quantity'] * distributor.cld_configurations
            cgst_amt = subtotal * distributor.cgst / 100
            igst_amt = subtotal * distributor.igst / 100
            sgst_amt = subtotal * distributor.sgst / 100
            orderlines['cgst_amount'] = cgst_amt
            orderlines['igst_amount'] = igst_amt
            orderlines['sgst_amount'] = sgst_amt
            orderlines['price'] = subtotal

            self.review_order_details[distributor_id]['tax'] += float(
                cgst_amt + igst_amt + sgst_amt)
            self.review_order_details[distributor_id]['total_amount'] += orderlines['price'] + \
                cgst_amt + igst_amt + sgst_amt
            self.review_order_details[distributor_id]['amount'] += subtotal
            self.review_order_details[distributor_id]['orderlines'].append(
                orderlines)

    def _calculate_available_stock(self, closing_stock, intransit_stock, norm, cld):
        closing_stock_cases = int(round(closing_stock / cld))
        intransit_stock_cases = int(round(intransit_stock / cld))
        return closing_stock_cases + intransit_stock_cases - norm

    def _save_review_orders(self):
        orders = self.review_order_details
        for order in orders.values():
            with transaction.atomic():
                try:
                    rpo_obj = ReviewPrimaryOrder(
                        distributor_id=order['distributor'],
                        shipping_address_id=order['shipping_address'],
                        amount=order['amount'],
                        total_amount=order['total_amount'],
                        tax=order['tax']
                    )
                    rpo_obj.save()
                    orderdetail = []
                    for orderlines in order['orderlines']:
                        orderlines['review_primary_order'] = rpo_obj
                        orderdetail.append(
                            ReviewPrimaryOrderDetail(**orderlines))
                    ReviewPrimaryOrderDetail.objects.bulk_create(
                        orderdetail)
                except Exception as e:
                    logger.error(
                        'Distributor order not created:%s' % e.message)


class CreatePrimaryOrder(object):
    '''
    Create primary order from review order table
    '''
    FLIGHT_MODE = False

    def __init__(self):
        self.distributors_list = []
        self.review_order_list = []  # make review order is_placed
        self.primary_orders_list = []
        self.discarded_orders = []

        today = dt.now()
        self.orderlines = ReviewPrimaryOrderDetail.objects.filter(
            review_primary_order__is_placed=False,
            review_primary_order__is_discarded=False,
            order_generated__gt=0,
            review_primary_order__modified__year=today.year,
            review_primary_order__modified__month=today.month,
            review_primary_order__modified__day=today.day,
        ).select_related(
            'review_primary_order', 'product')

    def generate_order(self):
        '''
        generate distributor wise alliance wise order
        '''
        alliance_partners = []
        alliance_orders = {}
        self.distributors_list = []
        self.discarded_orders = []

        for orderline in self.orderlines:
            alliance_id = orderline.product.brand.user_id
            distributor_id = orderline.review_primary_order.distributor_id
            min_order = orderline.review_primary_order.distributor.regionaldistributor.min_order

            if orderline.review_primary_order.total_amount < min_order:
                if orderline.review_primary_order not in self.discarded_orders:
                    self.discarded_orders.append(
                        orderline.review_primary_order.pk)
                continue

            if orderline.review_primary_order_id not in self.review_order_list:
                self.review_order_list.append(
                    orderline.review_primary_order_id)

            if alliance_id not in alliance_partners:
                alliance_partners.append(alliance_id)
                alliance_orders[alliance_id] = {}

            if distributor_id not in alliance_orders[alliance_id]:
                self.distributors_list.append(distributor_id)
                alliance_orders[alliance_id][distributor_id] = {}

                self._append_alliance_dict(
                    alliance_orders, alliance_id, distributor_id, orderline)

            alliance_orderline = {}

            self._append_orderline(
                alliance_orders[alliance_id][distributor_id],
                alliance_orderline,
                orderline)

            alliance_orders[alliance_id][distributor_id]['allianceorderlines'].append(
                alliance_orderline)

        self._add_discount_line(alliance_orders)
        self._update_discarded_order_status()
        print(alliance_orders.values())
        if alliance_orders.values():
            try:
                self.place_order(alliance_orders.values())
                self._update_distributor_manual()
                self._update_review_order_status()

                if settings.DEBUG:
                    file_obj = GenerateFile()
                    file_obj.generate_file(self.primary_orders_list)
                else:
                    from hul.tasks import generate_file
                    # add delay for sending xls file
                    generate_file.delay(self.primary_orders_list)

            except Exception as e:
                message = json.dumps(e)
                to_email = 'Shrishchandra.shukla@simtechitsolutions.in'
                subject = 'HUL CRON - alliance order not added'
                email = EmailMessage(subject, message, to=[to_email])
                email.send()

    def _append_alliance_dict(self, alliance_orders, alliance_id, distributor_id, order):
        alliance_orders[alliance_id][distributor_id]['alliance'] = order.product.brand.user_id
        alliance_orders[alliance_id][distributor_id]['alliance_code'] = \
            order.product.brand.code
        alliance_orders[alliance_id][distributor_id]['review_primary_order_id'] = order.review_primary_order_id
        alliance_orders[alliance_id][distributor_id]['distributor'] = distributor_id
        alliance_orders[alliance_id][distributor_id]['distributor_name'] = \
            order.review_primary_order.distributor.name
        alliance_orders[alliance_id][distributor_id]['shipping_address'] = \
            order.review_primary_order.shipping_address_id
        alliance_orders[alliance_id][distributor_id]['amount'] = 0.0
        alliance_orders[alliance_id][distributor_id]['total_amount'] = 0.0
        alliance_orders[alliance_id][distributor_id]['tax'] = 0.0
        alliance_orders[alliance_id][distributor_id]['invoice_number'] = ''
        alliance_orders[alliance_id][distributor_id]['allianceorderlines'] = []
        alliance_orders[alliance_id][distributor_id]['discountlines'] = []
        alliance_orders[alliance_id][distributor_id]['shaktibonuslines'] = []

    def _append_orderline(self, alliance_order, alliance_orderline, order):
        cld = order.product.cld_configurations
        quantity = order.order_generated * cld
        unitprice = order.unitprice

        alliance_orderline['product_name'] = order.product.basepack_name
        alliance_orderline['product_id'] = order.product_id
        alliance_orderline['quantity'] = quantity
        alliance_orderline['unitprice'] = unitprice
        price = taxable_amount = unitprice * quantity
        tax_dict = {'cgst': order.product.cgst,
                    'sgst': order.product.sgst, 'igst': order.product.igst}
        price_obj = CalculatePrice()
        net_amount, cgst, sgst, igst = price_obj.calculate_tax(
            taxable_amount, **tax_dict)

        alliance_orderline['price'] = price
        alliance_orderline['cgst_amount'] = cgst
        alliance_orderline['sgst_amount'] = sgst
        alliance_orderline['igst_amount'] = igst
        alliance_orderline['cgst'] = order.product.cgst
        alliance_orderline['sgst'] = order.product.sgst
        alliance_orderline['igst'] = order.product.igst

        alliance_order['amount'] += price
        cgst_amount = alliance_orderline['cgst_amount']
        sgst_amount = alliance_orderline['sgst_amount']
        igst_amount = alliance_orderline['igst_amount']
        alliance_order['tax'] += cgst_amount + sgst_amount + igst_amount
        alliance_order['total_amount'] += net_amount

    def place_order(self, orders):
        '''
        orders will be saved in Primary orders
        is_manual will be turned on
        '''
        for order in orders:
            for apo in order.values():
                with transaction.atomic():
                    try:
                        apo_obj = AlliancePartnerOrder(
                            alliance_id=apo['alliance'],
                            review_primary_order_id=apo['review_primary_order_id'],
                            distributor_id=apo['distributor'],
                            distributor_name=apo['distributor_name'],
                            alliance_code=apo['alliance_code'],
                            shipping_address_id=apo['shipping_address'],
                            tax=apo['tax'],
                            amount=apo['amount'],
                            total_amount=apo['total_amount']
                        )

                        apo_obj.invoice_number = ''

                        if len(apo['discountlines']) > 0 or len(apo['shaktibonuslines']):
                            apo_obj.has_claim = True
                            apo_obj.claim_status = ClaimStatus.PENDING

                        apo_obj.save()

                        self.primary_orders_list.append(apo_obj.pk)

                        orderdetail = []
                        discountdetail = []
                        shaktibonusdetail = []
                        for orderlines in apo['allianceorderlines']:
                            orderlines['alliance_partner_order'] = apo_obj
                            orderdetail.append(
                                AlliancePartnerOrderDetail(**orderlines))

                        AlliancePartnerOrderDetail.objects.bulk_create(
                            orderdetail)

                        for discountlines in apo['discountlines']:
                            discountlines['alliance_partner_order'] = apo_obj
                            discountdetail.append(
                                AlliancePartnerDiscountDetail(**discountlines))

                        AlliancePartnerDiscountDetail.objects.bulk_create(
                            discountdetail)

                        for bonusline in apo['shaktibonuslines']:
                            bonusline['alliance_partner_order'] = apo_obj
                            shaktibonusdetail.append(
                                AlliancePartnerShaktiDiscount(**bonusline))

                        AlliancePartnerShaktiDiscount.objects.bulk_create(
                            shaktibonusdetail)

                    except Exception as e:
                        raise StandardError(e.message)

    def _add_discount_line(self, alliance_orders):
        '''
        check if its the first order of the month, then add discount line
        '''
        today = dt.now()
        current_month = today.month
        primary_order_count = AlliancePartnerOrder.objects.filter(
            created__month=current_month).count()

        if primary_order_count > 0 and not self.FLIGHT_MODE:
            return

        prev_month = (today.replace(day=1) - dt.timedelta(days=1)).month

        distributor_lines = DistributorOrderDetail.objects.filter(
            Q(dispatched_on__month=prev_month),
            Q(item_status=OrderStatus.DISPATCHED),
            Q(distributor_order__distributor__in=self.distributors_list)
        )

        discount_lines = distributor_lines.filter(Q(discount_amount__gt=0)
                                                  ).annotate(Count('product'),
                                                             product_quantity=Sum(
                                                      'dispatch_quantity')
        ).values('product', 'product__basepack_name',
                 'product__brand__user_id',
                 'distributor_order__distributor',
                 'product_quantity'
                 ).annotate(discount_amount=Sum('discount_amount')
                            ).order_by('distributor_order__distributor')

        self.add_bonus_line(distributor_lines, alliance_orders)

        for line in discount_lines:
            alliance_id = line['product__brand__user_id']
            distributor_id = line['distributor_order__distributor']

            discount_line = {
                'product_id': line['product'],
                'discount_amount': line['discount_amount'],
                'total_quantity': line['product_quantity'] or 0,
                'product_name': line['product__basepack_name'],

            }
            alliance_orders[alliance_id][distributor_id]['discountlines'].append(
                discount_line)

    def add_bonus_line(self, distributor_lines, alliance_orders):
        '''
        adding a bonus line for each shakti if eligible
        TODO: alliance wise bonus and discount
        '''
        shaktis = distributor_lines.distinct(
            'distributor_order__shakti_enterpreneur')
        shakti_list = [
            shakti.distributor_order.shakti_enterpreneur for shakti in shaktis]

        for shakti in shakti_list:

            # get shakti order amount for the month
            shakti_order_amount = distributor_lines.filter(
                distributor_order__shakti_enterpreneur=shakti.id
            ).values('distributor_order__shakti_enterpreneur'
                     ).annotate(total_order=Sum('price'))

            if hasattr(shakti.shakti_user, 'shaktibonus'):
                # check if bonus exist for Shakti
                shakti_bonus = shakti.shakti_user.shaktibonus.shaktibonuslines_set.filter(
                    target_amount__lt=shakti_order_amount[0]['total_order']).order_by('-discount').first()

            else:
                # check if common bonus exist
                shakti_bonus = ShaktiBonusLines.objects.filter(
                    target_amount__lt=shakti_order_amount[0]['total_order'],
                    shakti_bonus__shakti_enterpreneur__isnull=True).order_by(
                        '-discount').first()

            if shakti_bonus:

                distributor_id = shakti.shakti_user.regional_sales.regional_distributor.user_id
                alliance_id = shakti.shakti_user.regional_sales.regional_distributor.alliance_partner.first().user_id

                # check if discount is cash or percent
                if shakti_bonus.discount_type == ShaktiBonusLines.PERCENT:
                    discount_amount = round(
                        shakti_order_amount[0]['total_order'] * shakti_bonus.discount / 100, 4)
                elif shakti_bonus.discount_type == ShaktiBonusLines.CASH:
                    discount_amount = round(shakti_bonus.discount, 4)

                discount_line = {
                    'discount_amount': discount_amount,
                    'shakti_bonus_line_id': shakti_bonus.pk,
                    'shakti_enterpreneur_id': shakti.id
                }

                alliance_orders[alliance_id][distributor_id]['shaktibonuslines'].append(
                    discount_line)

    def _update_distributor_manual(self):
        '''
        update distributor from manaul to automatic
        '''
        if len(self.distributors_list) > 0:
            RegionalDistributor.objects.filter(
                user_id__in=self.distributors_list).update(is_manual=False)

    def _update_review_order_status(self):
        '''
        update review order status to placed
        '''
        if len(self.review_order_list) > 0:
            ReviewPrimaryOrder.objects.filter(
                pk__in=self.review_order_list).update(is_placed=False)

    def _update_discarded_order_status(self):
        '''
        update review order status to discarded
        '''
        if len(self.discarded_orders) > 0:
            ReviewPrimaryOrder.objects.filter(
                pk__in=self.discarded_orders).update(is_discarded=True)


class DispatchDistributorOrder(object):
    ''' dispatch order for distributors '''
    _SQL = '''
    SELECT "orders_distributorstock".id, "orders_distributororderdetail"."product_id" AS "product_id", SUM("orders_distributororderdetail"."quantity") AS "count", orders_distributorstock.closing_stock
    FROM "orders_distributororder"
    INNER JOIN "orders_distributororderdetail" ON ("orders_distributororder"."id" = "orders_distributororderdetail"."distributor_order_id")
    LEFT JOIN "orders_distributorstock" ON orders_distributorstock.product_id = orders_distributororderdetail.product_id and orders_distributorstock.distributor_id = orders_distributororder.distributor_id and DATE(orders_distributorstock.modified) > CURRENT_DATE - interval '1 day'
    WHERE "orders_distributororder"."id" IN %s
    GROUP BY "orders_distributororderdetail"."product_id", orders_distributorstock.id
    '''

    def __init__(self, distributor_orders=None):
        self.orders = distributor_orders
        self.product_total = {}
        self.ignore_orders = []
        self.dispatched_orders = []

    def create_dispatch_orders(self):
        ''' dispatch multiple orders
            get product quantity with closing stock
            calculate ratio if required
            check and apply promotions if applicable
            calculate prices and update status
        '''
        order_ids = self.orders.values_list('id', flat=True)
        products = self.get_product_quantity(order_ids)
        product_count = {}
        for product in products:
            ratio = False
            closing_stock = product.closing_stock or 0
            if int(product.count) > closing_stock:
                ratio = True
            product_count[product.product_id] = {}
            product_count[product.product_id]['total_quantity'] = product.count
            product_count[product.product_id]['closing_stock'] = closing_stock
            product_count[product.product_id]['updated_closing_stock'] = closing_stock
            product_count[product.product_id]['ratio'] = ratio
            self.product_total.update(product_count)

        self._prepare_order_data()
        return self.ignore_orders, self.dispatched_orders

    def get_product_quantity(self, order_ids):
        products = DistributorOrderDetail.objects.raw(
            self._SQL, [tuple(order_ids), ])
        return products

    def _prepare_order_data(self):
        '''
        modify order information according to stock availability
        '''
        for order in self.orders:

            if not self._calculate_quantity_ratio(order):
                self.ignore_orders.append(order.invoice_number)
                continue

            self._check_promotion(order)
            order_sum = order.distributor_order_details.aggregate(total_amount=Sum('net_amount'),
                                                                  tax=Sum(
                                                                      F('cgst') + F('sgst') + F('igst')),
                                                                  discount_amount=Sum(
                                                                      F('discount_amount') + F('distributor_discount')),
                                                                  amount=Sum('price'))

            order.amount = order_sum['amount']
            order.tax = order_sum['tax']
            order.discount_amount = order_sum['discount_amount']
            order.total_amount = order_sum['total_amount']
            order.order_status = OrderStatus.DISPATCHED
            order.save()

            if order.invoice_number not in self.dispatched_orders:
                self.dispatched_orders.append(
                    order.invoice_number)

    def _calculate_quantity_ratio(self, order):
        '''
        check and update quantity if required
        '''
        for orderline in order.distributor_order_details.all():
            if self.product_total[orderline.product_id]['closing_stock'] == 0:
                orderline.dispatch_quantity = 0
                orderline.item_status = OrderStatus.CANCELLED
                orderline.save()
                continue

            if self.product_total[orderline.product_id]['ratio']:
                orderline.dispatch_quantity = round((
                    orderline.quantity /
                    self.product_total[orderline.product_id]['total_quantity']
                ) * self.product_total[orderline.product_id]['closing_stock'], 0)

            else:
                orderline.dispatch_quantity = orderline.quantity

            # change dispatch quantity to closing stock if not not enough stock
            if orderline.dispatch_quantity > self.product_total[orderline.product_id]['updated_closing_stock']:
                orderline.dispatch_quantity = self.product_total[
                    orderline.product_id]['updated_closing_stock']

            self.product_total[orderline.product_id]['updated_closing_stock'] = self.product_total[
                orderline.product_id]['updated_closing_stock'] - orderline.dispatch_quantity
            orderline.item_status = OrderStatus.DISPATCHED
            orderline.save()
        return True

    def _check_promotion(self, order):
        ''' check and apply applicable promotions for order 
            update closing stock
        '''
        for orderline in order.distributor_order_details.all():

            # skip loop if ordered quantity is equal to dispatch quantity
            if orderline.quantity == orderline.dispatch_quantity:
                continue

            promotions = orderline.product.offers_promotionlines_related.filter(
                Q(promotion__shakti_enterpreneur=None) |
                Q(promotion__shakti_enterpreneur=orderline.distributor_order.shakti_enterpreneur.id))

            order_mgmt_obj = OrderManagement()
            cal_price_obj = CalculatePrice()

            # remove promotion if any
            orderline.promotion = []
            orderline.promotion_applied = ''

            # remove initial discount price
            orderline.discount_amount = 0
            self.calculate_orderline_amount(orderline)

            for promotion in promotions:
                try:
                    order_mgmt_obj._validate_quantity(
                        promotion.buy_quantity, orderline.dispatch_quantity)
                    self.calculate_orderline_amount(orderline, promotion)
                except:
                    continue

    def calculate_orderline_amount(self, orderline, promotion=None):
        '''
        calculate all price for a particular orderline
        '''
        order_mgmt_obj = OrderManagement()
        cal_price_obj = CalculatePrice()

        if promotion is not None:
            orderline.discount_amount = order_mgmt_obj._calculate_discount(
                promotion.discount, orderline.unitprice * orderline.dispatch_quantity)
            # apply promotion
            orderline.promotion = [promotion.pk]
            orderline.promotion_applied = promotion.promotion.name

        orderline.price = orderline.unitprice * float(orderline.dispatch_quantity)

        distributor_discount_percent = orderline.distributor_discount_percent

        distributor_discount = 0
        if distributor_discount_percent is not None:
            discountable_amount = orderline.price - orderline.discount_amount

            distributor_discount = (
                discountable_amount * distributor_discount_percent) / 100.0
            orderline.distributor_discount = round(distributor_discount, 4)
        # calculate taxable amount
        taxable_amount = orderline.price - orderline.discount_amount - distributor_discount

        if orderline.product_info:
            product_info = json.loads(orderline.product_info)
            cgst = product_info['cgst']
            igst = product_info['igst']
            sgst = product_info['sgst']
            stockist_margin = product_info.get('brand__stockist_margin', 0)
        else:
            stockist_margin = cgst = igst = sgst = 0
            # igst = orderline.product.igst
            # sgst = orderline.product.sgst
            # stockist_margin = orderline.product.brand.stockist_margin
        taxes = {'cgst': cgst, 'sgst': sgst, 'igst': igst}
        # calculate tax
        net_amount, orderline.cgst, orderline.sgst, orderline.igst = cal_price_obj.calculate_tax(
            taxable_amount, **taxes)

        # calculate net amount
        orderline.net_amount = round(net_amount, 2)
        # orderline.net_amount = round(net_amount + (net_amount * stockist_margin / 100), 2) #stockist margin included in base rate

        orderline.save()
        return orderline
