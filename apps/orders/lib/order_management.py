''' orders/order_management.py '''
import json
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from orders.serializers import AlliancePartnerOrderSerializer, AlliancePartnerOrderDetailSerializer
from orders.models import (
    DistributorOrder, DistributorOrderDetail, DistributorStock)
from app.models import RegionalSalesPromoter, RegionalDistributor, ShaktiEntrepreneur
from product.models import Product
from job.models import Email, MobileNotification
from offers.models import PromotionLines, DiscountType, DiscountToShakti, ShaktiBonusLines


from hul.constants import FROM_EMAIL, COUNTRY_CODE
from hul.choices import OrderStatus, PaymentStatus, SentStatusType


class OrderManagement(object):
    ''' OrderManagement class '''
    PRODUCT_CLD_MAX = 10
    PRODUCT_UNIT_MAX = 99999
    UPLIFT_FACTOR = 0
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timezone.timedelta(days=1)
    yesterday = today - timezone.timedelta(days=1)

    @classmethod
    def alliance_order_template(cls, distributor_orderlines):
        ''' generate alliance order from Distributor order lines '''
        alliance_partners = []
        alliance_orders = {}

        for order in distributor_orderlines:
            alliance_order = []
            alliance_id = order.product.brand_id
            if alliance_id not in alliance_partners:
                alliance_partners.append(alliance_id)
                alliance_orders[alliance_id] = {}
                cls._append_alliance_dict(alliance_orders, alliance_id, order)
                distributor_details = RegionalDistributor.objects.filter(
                    user=order.distributor_order.distributor).first()
                alliance_orders[alliance_id]['distributor_code'] = distributor_details.code

            alliance_orderline = {}
            cls._append_orderline(alliance_orderline, order)
            alliance_orders[alliance_id]['allianceorderlines'].append(
                alliance_orderline)

        alliance_orders_list = []

        for alliance_order in alliance_orders.values():
            products_list = []
            product_ids = []
            products = {}
            for orderline in alliance_order['allianceorderlines']:
                if orderline['product'] not in product_ids:
                    product_ids.append(orderline['product'])
                    products[orderline['product']] = orderline
                else:
                    products[orderline['product']
                             ]['quantity'] += orderline['quantity']

                quantity = products[orderline['product']]['quantity']
                available_stock, rtp_stock = cls._get_available_stock(orderline['product'],
                                                                      alliance_order['distributor'])
                suggested_stock = max(0, quantity - available_stock)
                products[orderline['product']
                         ]['available_stock'] = available_stock
                products[orderline['product']
                         ]['suggested_stock'] = suggested_stock
                products[orderline['product']]['rtp_stock'] = rtp_stock
                products[orderline['product']]['uplift'] = cls.UPLIFT_FACTOR
                products[orderline['product']]['final_stock'] = cls._calculate_final_stock(
                    quantity, rtp_stock, cls.UPLIFT_FACTOR, suggested_stock)
                products[orderline['product']]['price'] = \
                    products[orderline['product']]['final_stock'] * \
                    orderline['unitprice']
                alliance_order['amount'] = orderline['price'] + \
                    alliance_order['amount']
                alliance_order['quantity'] = \
                    products[orderline['product']]['final_stock'] + \
                    alliance_order['quantity']

            products_list.extend(products.values())
            alliance_order['allianceorderlines'] = products_list

            alliance_order['total_amount'] = alliance_order['amount'] + \
                alliance_order['tax']
            alliance_orders_list.append(alliance_order)

        return alliance_orders_list

    @classmethod
    def generate_alliance_order(cls, distributor_orderlines, final_stock):
        ''' generate alliance order from Distributor order lines '''
        alliance_partners = []
        alliance_orders = {}
        shakti_stock = {}
        product_count = {}

        for order in distributor_orderlines:
            alliance_id = order.product.brand.user_id
            if alliance_id not in alliance_partners:
                alliance_partners.append(alliance_id)
                alliance_orders[alliance_id] = {}
                cls._append_alliance_dict(alliance_orders, alliance_id, order)
            alliance_orderline = {}
            quantity = order.quantity
            cls._append_orderline(alliance_orderline, order)
            alliance_orders[alliance_id]['allianceorderlines'].append(
                alliance_orderline)

            # original ordered stock
            if order.product_id not in shakti_stock:
                shakti_stock.update({order.product_id: 0})
            shakti_stock[order.product_id] += quantity

            # calculate product counts incase less is ordered by RS
            if order.product_id not in product_count:
                product_count.update({order.product_id: 0})
            product_count[order.product_id] += 1

        difference_stock = cls.difference_dict(final_stock, shakti_stock)
        alliance_orders_list = cls._modify_alliance_order(alliance_orders,
                                                          difference_stock, final_stock, product_count)

        return alliance_orders_list

    @classmethod
    def save_alliance_order(cls, alliance_order):
        ''' save alliance order '''
        brand = ''

        alliance_order['alliance_code'] = alliance_order['allianceorderlines'][0]['brand_code']
        alliance_ser = AlliancePartnerOrderSerializer(data=alliance_order)
        if alliance_ser.is_valid():
            alliance_saved_obj = alliance_ser.save()
            order_update = DistributorOrder.objects.get(
                pk=alliance_order['distributor_order_id'])
            order_update.order_status = OrderStatus.CONFIRMED
            order_update.save(update_fields=['order_status'])
            for alliance_order_detail in alliance_order['allianceorderlines']:
                # primary of AlliancePartnerOrder
                alliance_order_detail['alliance_partner_order'] = alliance_saved_obj.pk
                brand = alliance_order_detail['brand_code']
                alliance_detail_ser = AlliancePartnerOrderDetailSerializer(
                    data=alliance_order_detail)
                if alliance_detail_ser.is_valid():
                    alliance_detail_ser.save()
                    cls._update_distributor_detail(alliance_order_detail)
                else:
                    err = alliance_detail_ser.errors
                    message = json.dumps(err)
                    to_email = ('mayank.kukreja@netsolutions.in', 'parsenjit.jha@gmail.com')
                    subject = 'alliance_order_detail'
                    email = EmailMessage(subject, message, to=[to_email])
                    email.send()
            return '%s%s' % (brand, str(alliance_saved_obj.pk).zfill(6))
        else:
            err = alliance_ser.errors

    @classmethod
    def _modify_alliance_order(cls, alliance_orders, difference_stock, final_stock, product_count):
        ''' check difference in stock and modify orderline accordingly '''

        alliance_orders_list = alliance_orders.values()
        for alliance_order in alliance_orders_list:
            index = {}
            current_product_count = {}
            for orderline in alliance_order['allianceorderlines']:
                product_id = orderline['product']

                cls._update_product_index(
                    index, product_id, current_product_count)

                # calculate quantity per shakti if less quantity is ordered
                if difference_stock[product_id] < 0:
                    updated_quantity = \
                        final_stock[product_id] / product_count[product_id]
                    orderline['quantity'] = updated_quantity

                current_product_count[product_id] += orderline['quantity']
                alliance_order['quantity'] += orderline['quantity']

                # adding subtracting extra quantity from orderline
                if index[product_id] == product_count[product_id] \
                        and current_product_count[product_id] != final_stock[product_id]\
                        and difference_stock[product_id] < 0:
                    prev_quantity = orderline['quantity']
                    orderline['quantity'] = updated_quantity + \
                        final_stock[product_id] - \
                        current_product_count[product_id]
                    alliance_order['quantity'] += orderline['quantity'] - \
                        prev_quantity

                # extra quantity is ordered add an orderline
                if index[product_id] == product_count[product_id]\
                        and current_product_count[product_id] != final_stock[product_id]\
                        and difference_stock[product_id] > 0:

                    rs_orderline = cls._add_orderline(orderline, difference_stock[product_id],
                                                      alliance_order['distributor'])
                    product_count[product_id] += 1
                    alliance_order['allianceorderlines'].append(rs_orderline)
                orderline['price'] = round(
                    orderline['quantity'] * orderline['unitprice'], 5)
                alliance_order['amount'] = round(
                    orderline['price'] + alliance_order['amount'], 5)

            alliance_order['total_amount'] = alliance_order['amount'] + \
                alliance_order['tax']

        return alliance_orders_list

    @classmethod
    def _update_product_index(cls, index, product_id, current_product_count):
        if product_id not in index:
            index.update({product_id: 0})
            current_product_count.update({product_id: 0})
        index[product_id] += 1

    @classmethod
    def _add_orderline(cls, orderline_detail, quantity, distributor_id):
        ''' add alliance orderline '''
        address = RegionalDistributor.objects.values(
            'address_id').get(user_id=distributor_id)
        orderline = {}
        orderline['product'] = orderline_detail['product']
        orderline['quantity'] = quantity
        orderline['unitprice'] = orderline_detail['unitprice']
        orderline['price'] = orderline_detail['unitprice'] * quantity
        orderline['brand_code'] = orderline_detail['brand_code']
        orderline['shipping_address'] = address['address_id']
        orderline['distributor_order_detail'] = None

        return orderline

    @classmethod
    def _append_alliance_dict(cls, alliance_orders, alliance_id, order):
        alliance_orders[alliance_id]['alliance'] = order.product.brand.user_id
        alliance_orders[alliance_id]['distributor_order_id'] = order.distributor_order.pk
        alliance_orders[alliance_id]['distributor'] = order.distributor_order.distributor.pk
        alliance_orders[alliance_id]['distributor_name'] = \
            order.distributor_order.distributor.name
        alliance_orders[alliance_id]['shipping_address'] = \
            order.distributor_order.shipping_address.pk
        alliance_orders[alliance_id]['amount'] = 0.0
        alliance_orders[alliance_id]['quantity'] = 0
        alliance_orders[alliance_id]['tax'] = 0.0
        alliance_orders[alliance_id]['total_amount'] = 0.0
        alliance_orders[alliance_id]['invoice_number'] = ''
        alliance_orders[alliance_id]['allianceorderlines'] = []

    @classmethod
    def _append_orderline(cls, alliance_orderline, order):
        quantity = order.quantity
        unitprice = order.product.net_rate
        price = quantity * unitprice
        alliance_orderline['distributor_order_detail'] = order.id
        alliance_orderline['shipping_address'] = order.shipping_address_id
        alliance_orderline['sales_promoter_id'] = order.distributor_order.sales_promoter.id
        alliance_orderline['sales_promoter_name'] = order.distributor_order.sales_promoter.name
        alliance_orderline['shakti_entrepreneur_id'] = \
            order.distributor_order.shakti_enterpreneur.id
        alliance_orderline['shakti_enterpreneur_name'] = \
            order.distributor_order.shakti_enterpreneur.username
        alliance_orderline['brand'] = order.product.brand.user.name
        alliance_orderline['brand_code'] = order.product.brand.code
        alliance_orderline['product_name'] = order.product.basepack_name
        alliance_orderline['product'] = order.product_id
        alliance_orderline['quantity'] = quantity
        alliance_orderline['unitprice'] = unitprice
        alliance_orderline['price'] = price

    @classmethod
    def _get_available_stock(cls, product_id, distributor_id):
        '''
        get available stock:
        get opening stock, receipt from alliance(alliance order detail),
        ready for pickup (from distributor orderdetail)
        available stock = opening + receipt - RTP
        '''
        rtp_stock = 0
        stock = DistributorStock.objects.filter(product_id=product_id,
                                                distributor_id=distributor_id).order_by('-created').first()

        distributor_rtp = DistributorOrderDetail.objects.filter(created__gte=cls.today,
                                                                created__lte=cls.tomorrow,
                                                                item_status=OrderStatus.READYPICKUP,
                                                                product_id=product_id,
                                                                distributor_order__distributor_id=distributor_id)\
            .aggregate(rtp=Sum('quantity'))

        if stock:
            closing_stock = stock.closing_stock

        if distributor_rtp['rtp'] is not None:
            rtp_stock = distributor_rtp['rtp']

        available_stock = closing_stock - rtp_stock
        return max(0, available_stock), rtp_stock

    @classmethod
    def prepare_distributor_order(cls, request_data):
        ''' distributor order '''
        
        if request_data['sales_promoter'] != 0:
            promoter_obj = RegionalSalesPromoter.objects.get(
                user_id=request_data['sales_promoter'])
            shakti_obj = ShaktiEntrepreneur.objects.filter(
                user_id=request_data['shakti_enterpreneur'], is_active=True).first()
            if not shakti_obj:
                raise Exception('Shakti enterpreneur is not active')
        else:
            shakti_obj = ShaktiEntrepreneur.objects.get(
                user_id=request_data['shakti_enterpreneur'])
            request_data['sales_promoter'] = shakti_obj.regional_sales.user_id
            promoter_obj = RegionalSalesPromoter.objects.get(
                id=shakti_obj.regional_sales_id)
        request_data['distributor'] = promoter_obj.regional_distributor.user.pk
        request_data['shipping_address'] = shakti_obj.address_id
        amount = 0
        discount_amount = 0
        tax = 0
        total_amount = 0
        distributor_discount = 0
        products = request_data.get('products')

        for product in products:
            product['shipping_address'] = request_data['shipping_address']
            product_details = Product.objects.filter(
                pk=product['product'])

            product['product_info'] = json.dumps(
                product_details.values('partner_code', 'brand_id',
                                       'basepack_code', 'cgst', 'sgst',
                                       'igst', 'basepack_name', 'base_rate',
                                       'cld_configurations', 'brand__stockist_margin',
                                       'category_id', 'mrp')[0])
            quantity = product['quantity']
            product['promotion_applied'] = []
            product['distributor_promotion'] = product.get('distributor_promotion') if product.get('distributor_promotion') > 0 else None

            if product['is_cld']:
                quantity = quantity * product_details[0].cld_configurations
                product['quantity'] = quantity

            #changed for secondary orders
            unitprice = round(product_details[0].base_rate + (product_details[0].base_rate * product_details[0].brand.stockist_margin / 100), 5)
            
            product['unitprice'] = unitprice

            if product['is_free'] is False:
                taxable_amount = product['price'] = unitprice * quantity

            # offer logic
            if bool(product['promotion']) and not product['is_free']:
                promotions = cls.validate_promotion(
                    product, products, request_data['shakti_enterpreneur'])

                taxable_amount = product['price'] - \
                    product['discount_amount']
                discount_amount += product['discount_amount']

            if product['distributor_promotion'] is not None:
                discounttoshakti = DiscountToShakti.objects.filter(pk=product['distributor_promotion'],
                                                                   regional_distributor_id=request_data['distributor']
                                                                   ).first()

                if discounttoshakti is not None:
                    discount_type = discounttoshakti.discount_type

                    if discount_type == ShaktiBonusLines.PERCENT:
                        discountable_amount = product['price'] - \
                            product['discount_amount']
                        distributor_discount = discountable_amount * \
                            (discounttoshakti.discount / 100.0)
                    else:
                        distributor_discount = discounttoshakti.discount

            product['distributor_discount'] = round(distributor_discount, 5)
            if distributor_discount != 0:
                product['distributor_promotion'] = product['distributor_promotion']
                product['distributor_discount_percent'] = discounttoshakti.discount
                taxable_amount = taxable_amount - distributor_discount

            cgst_amount = round(
                taxable_amount * product_details[0].cgst / 100, 5)
            sgst_amount = round(
                taxable_amount * product_details[0].sgst / 100, 5)
            igst_amount = round(
                taxable_amount * product_details[0].igst / 100, 5)

            product['cgst'] = cgst_amount
            product['sgst'] = sgst_amount
            product['igst'] = igst_amount

            if len(product['promotion_applied']) == 0:
                product['promotion_applied'] = u''
            else:
                product['promotion_applied'] = ', '.join(
                    product['promotion_applied'])

            product['net_amount'] = round(taxable_amount + \
                product['cgst'] + product['sgst'] + product['igst'], 5)

            # product['net_amount'] = round(product['net_amount'] +
            #                               (product['net_amount'] *
            #                                product_details[0].brand.stockist_margin / 100), 2)

            tax += product['cgst'] + product['sgst'] + product['igst']
            amount += product['price']
            total_amount += product['net_amount']

        request_data['discount_amount'] = discount_amount
        request_data['tax'] = tax
        request_data['amount'] = amount
        request_data['total_amount'] = total_amount

        return request_data

    @staticmethod
    def _update_distributor_detail(alliance_order_detail):
        ''' update distributor detail status when order status is updated by Alliance '''
        if alliance_order_detail['distributor_order_detail'] is not None:
            order_detail_update = DistributorOrderDetail.objects.get(
                pk=alliance_order_detail['distributor_order_detail'])
            order_detail_update.item_status = OrderStatus.CONFIRMED
            order_detail_update.save(update_fields=['item_status'])

    @classmethod
    def prepare_alliance_order_id(cls, order_id, alliance_code):
        '''alliance order id'''
        return alliance_code + str(order_id).zfill(6)

    @classmethod
    def prepare_rsp_order_id(cls, order_id):
        '''prepare rsp order'''
        return 'RSP%s' % str(order_id).zfill(6)

    @classmethod
    def validate_units(cls, request_data):
        ''' validate units entered '''
        products = request_data.get('products')
        for product in products:
            if product['is_cld'] and product['quantity'] > cls.PRODUCT_CLD_MAX:
                return False
            if not product['is_cld'] and product['quantity'] > cls.PRODUCT_UNIT_MAX:
                return False
        return True

    @classmethod
    def send_email_notification(cls, context, data):
        ''' sending email notification for order status '''

        html_content = None
        email_template = 'orders/email/order_' + \
            data['order_status'].lower().replace(" ", "") + '.html'
        html_content = render_to_string(email_template, context)
        subject = render_to_string(
            'orders/email/order_email_subject.txt', context)

        if data['payment_status'] == PaymentStatus.PAID:
            html_content = render_to_string(
                'orders/email/order_payment_paid.html', context)
            subject = render_to_string(
                'orders/email/order_payment_email_subject.txt', context)

        if html_content is not None:

            kwargs = {
                'from_email': FROM_EMAIL,
                'message': html_content
            }

            if settings.ORDER_EMAIL_NOTIFICATION:
                sent_status_type = SentStatusType.PENDING
            else:
                sent_status_type = SentStatusType.FLIGHT

            kwargs.update({
                'sent_status_type': sent_status_type
            })
            Email.objects.get_or_create(defaults={
                'to_email': data['to_email'], 'subject': subject}, **kwargs)

    @classmethod
    def send_sms_notification(cls, context, data):
        ''' sms notification will be added here '''

        to_phone = str(data['to_phone'])
        phone_number = cls._add_country_code(to_phone)

        mobile_message = render_to_string(
            'orders/email/order_sms.html', context)
        data['mobile_message'] = mobile_message

        kwargs = {
            'distributor_order_id': data['distributor_order_id'],
            'order_status': data['order_status']
        }

        if settings.ORDER_SMS_NOTIFICATION:
            sent_status_type = SentStatusType.PENDING
        else:
            sent_status_type = SentStatusType.FLIGHT

        kwargs.update({
            'sent_status_type': sent_status_type
        })
        MobileNotification.objects.get_or_create(defaults={
            'to_phone': phone_number, 'message': data['mobile_message']}, **kwargs)

    @classmethod
    def _add_country_code(cls, phone_number):
        ''' add country code if not added '''
        if not cls._check_country_code(phone_number):
            phone_number = COUNTRY_CODE + phone_number

        return phone_number

    @classmethod
    def _check_country_code(cls, phone_number):
        ''' check if country code is there in phone number '''

        if COUNTRY_CODE in phone_number:
            return True
        else:
            return False

    @staticmethod
    def calculate_price(unitprice, quantity):
        ''' price calculation will be done here '''
        return unitprice * float(quantity)

    @staticmethod
    def _calculate_final_stock(quantity, rtp_stock, uplift, suggested_stock):
        ''' calculate final stock '''
        final_stock = ((quantity + rtp_stock) / 2) * uplift + suggested_stock
        return final_stock

    @staticmethod
    def difference_dict(dict_a, dict_b):
        ''' calculate difference between 2 dictionary values '''
        output_dict = {key: dict_a[key] - dict_b[key]
                       for key in dict_a.keys() if key in dict_b.keys()}
        return output_dict

    @staticmethod
    def add_available_stock(orderlines, distributor_id, shakti):
        from django.db.models import Q
        from django.utils import timezone
        promocodes = []
        today = timezone.now().date()
        for orderline in orderlines:
            orderline.available_stock =\
                orderline.product.distributorstock.filter(
                    distributor_id=distributor_id).order_by('-created').first().closing_stock
            promotion_set = PromotionLines.objects.filter(Q(buy_product=orderline.product),
                                                          Q(promotion__start__lte=today),
                                                          Q(promotion__end__gte=today),
                                                          Q(promotion__shakti_enterpreneur=None) |
                                                          Q(promotion__shakti_enterpreneur_id=shakti)
                                                          ).order_by('-buy_quantity', '-discount')
            for promotion in promotion_set:
                promo_dict = {}
                promo_dict['buy_product'] = promotion.buy_product_id
                promo_dict['buy_quantity'] = promotion.buy_quantity
                promo_dict['discount'] = promotion.discount
                promo_dict['promotion_id'] = promotion.id
                promo_dict['promotion_name'] = promotion.promotion.name
                promocodes.append(promo_dict)

        return orderlines, json.dumps(promocodes)

    @classmethod
    def validate_promotion(cls, product, products, shakti_id):
        promotion_details = PromotionLines.objects.filter(
            id__in=product['promotion'], buy_product=product['product']).select_related('promotion')

        for promotion in promotion_details:

            cls._validate_product(
                promotion.buy_product_id, product['product'])
            cls._validate_quantity(
                promotion.buy_quantity, product['quantity'])

            if promotion.promotion.discount_type == DiscountType.PERCENT:
                cls._validate_shakti(
                    promotion.promotion.shakti_enterpreneur_id, shakti_id)

                discount_amount = cls._calculate_discount(
                    promotion.discount, product['price'])

                discount_applied = product['discount_amount']

                if discount_amount != discount_applied:
                    product['discount_amount'] = discount_amount

            elif promotion.promotion.discount_type == DiscountType.QUANTITY:
                cls._validate_free_product(
                    promotion.free_product_id, promotion.free_quantity, products)

            elif promotion.promotion.discount_type == DiscountType.TRADE_OFFER:

                discount_amount = cls._calculate_discount(
                    promotion.discount, product['price'])

                discount_applied = product['discount_amount']

                if discount_amount != discount_applied:
                    product['discount_amount'] = discount_amount
            else:
                raise StandardError('Promotion is not valid')

            product['promotion_applied'].append(promotion.promotion.name)

    @staticmethod
    def _validate_shakti(promotion_shakti, order_shakti):
        if promotion_shakti != order_shakti:
            raise StandardError(
                'Promotion is not valid for selected Shakti Entrepreneur')

    @staticmethod
    def _validate_product(promotion_product, ordered_product):
        if promotion_product != ordered_product:
            raise StandardError('Promotion applied on wrong product')

    @staticmethod
    def _validate_quantity(promotion_quantity, ordered_quantity):
        if promotion_quantity > ordered_quantity:
            raise StandardError('Order does not have required quantity')

    @staticmethod
    def _calculate_discount(promotion_discount, product_price):
        discount_amount = round(
            promotion_discount * product_price / 100, 5)
        return discount_amount

    @staticmethod
    def _validate_free_product(free_product_id, free_quantity, products):
        '''
        check if free product is added in the order
        '''
        for product in products:
            if product['is_free']:
                if product['product'] == free_product_id and product['quantity'] != free_quantity:
                    raise StandardError('Quantity of free product is not same')
                else:
                    return True
        else:
            # Didn't find free product
            raise StandardError('Add free product in order')


class CalculatePrice(object):
    '''
    all price calculation for cases and units will be performed
    '''

    def calculate_tax(self, taxable_amount, **kwargs):
        ''' calculate total tax on a product '''

        cgst = round(taxable_amount * kwargs['cgst'] / 100, 5)
        sgst = round(taxable_amount * kwargs['sgst'] / 100, 5)
        igst = round(taxable_amount * kwargs['igst'] / 100, 5)
        net_amount = taxable_amount + cgst + sgst + igst

        return net_amount, cgst, sgst, igst

    def calculate_price(self, unitprice, cases, cld):
        ''' calculate total price on a product, returning price and tax '''
        price = unitprice * cases * cld
        return price

    def calculate_gst_price(self, obj):
        subtotal = obj.unitprice * obj.order_generated
        obj.cgst_amount = subtotal * obj.product.cgst / 100
        obj.igst_amount = subtotal * obj.product.igst / 100
        obj.sgst_amount = subtotal * obj.product.sgst / 100
        tax = obj.cgst_amount + obj.igst_amount + obj.sgst_amount
        obj.price = (subtotal + tax) * obj.product.cld_configurations
        return obj
