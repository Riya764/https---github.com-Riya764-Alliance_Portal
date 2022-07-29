'''
orders/invoces.py
This class will generate distributor invoices
'''
from app.models import UserAddress
import json


class DistributorInvoice(object):
    '''
    invoice class to generate shakti orders/orderlines
    '''

    @classmethod
    def prepare_individual_sku_orders(cls, queryset, orderlines):
        '''
        prepare shakti wise orders
        '''
        orders = []
        product_ids = []
        shakti_orders = {}
        product_orders = {}
        product_orders['gross_amount'] = 0

        for order in orderlines:
            order_id = order.distributor_order_id
            product_id = order.product_id

            if order_id not in orders:
                orders.append(order_id)
                shakti_orders[order_id] = {}
                cls._append_shakti_dict(shakti_orders, order_id, order)

            if product_id not in product_ids:
                product_ids.append(product_id)
                product_orders[product_id] = {}
                cls._append_product_order_dict(
                    product_orders, product_id, order)

            net_amount = order.net_amount
            product_orders[product_id]['total_quantity'] += order.dispatch_quantity or 0
            product_orders[product_id]['total_amount'] += net_amount
            product_orders['gross_amount'] += net_amount

            shakti_orderline = {}
            cls._append_orderline(shakti_orderline, order)
            shakti_orders[order_id]['quantity'] += shakti_orderline['quantity']

            shakti_orders[order_id]['shaktiorderlines'].append(
                shakti_orderline)

        return list(shakti_orders.values()), list(product_orders.values()), product_orders['gross_amount']

    @classmethod
    def prepare_shakti_wise(cls, shakti_wise_orders, obj):
        shakti_wise_orders[obj.shakti_enterpreneur_id] = {}
        shakti_wise_orders[obj.shakti_enterpreneur_id]['total_amount'] = 0
        shakti_wise_orders[obj.shakti_enterpreneur_id]['total_quantity'] = 0
        shakti_wise_orders[obj.shakti_enterpreneur_id]['shakti_name'] = obj.shakti_enterpreneur.name
        shakti_wise_orders[obj.shakti_enterpreneur_id]['shakti_code'] = obj.shakti_enterpreneur.shakti_user.code

    @classmethod
    def _append_product_order_dict(cls, product_orders, product_id, order):
        '''
        make a sku wise orderline
        '''
        product_orders[product_id]['product_name'] = order.product.basepack_name
        product_orders[product_id]['product_code'] = order.product.basepack_code
        product_orders[product_id]['product_size'] = " ".join(
            [order.product.basepack_size, order.product.unit.unit])
        product_orders[product_id]['product_mrp'] = order.product.mrp
        product_orders[product_id]['product_tur'] = order.product.tur
        product_orders[product_id]['total_quantity'] = 0
        product_orders[product_id]['total_amount'] = 0

    @classmethod
    def _append_shakti_dict(cls, shakti_orders, order_id, order):
        '''
        add shakti address, distributor address, orderline
        '''
        shakti_address_id = order.distributor_order.shakti_enterpreneur.shakti_user.address_id
        shakti_orders[order_id]['invoiced_to'] = {}
        shakti_orders[order_id]['invoiced_from'] = {}
        shakti_orders[order_id]['distributor_name'] = \
            order.distributor_order.distributor.name
        shakti_orders[order_id]['shipping_address'] = \
            order.distributor_order.shipping_address.pk
        shakti_orders[order_id]['invoiced_from']['name'] = \
            order.distributor_order.distributor.name
        shakti_orders[order_id]['invoiced_from']['address'] = \
            order.distributor_order.shipping_address
        shakti_orders[order_id]['invoiced_from']['contact_number'] = \
            order.distributor_order.distributor.contact_number

        shakti_orders[order_id]['invoiced_to']['name'] = \
            order.distributor_order.shakti_enterpreneur.name
        shakti_orders[order_id]['invoiced_to']['code'] = \
            order.distributor_order.shakti_enterpreneur.shakti_user.code
        shakti_orders[order_id]['invoiced_to']['address'] = \
            UserAddress.objects.get(pk=shakti_address_id)
        shakti_orders[order_id]['invoiced_to']['contact_number'] = \
            order.distributor_order.shakti_enterpreneur.contact_number
        shakti_orders[order_id]['amount'] = order.distributor_order.amount
        shakti_orders[order_id]['quantity'] = 0
        shakti_orders[order_id]['tax'] = order.distributor_order.tax
        shakti_orders[order_id]['total_amount'] = order.distributor_order.total_amount
        shakti_orders[order_id]['invoice_number'] = order.distributor_order.invoice_number
        shakti_orders[order_id]['invoice_date'] = order.distributor_order.modified
        shakti_orders[order_id]['shaktiorderlines'] = []

    @classmethod
    def _append_orderline(cls, shakti_orderline, order):
        product_info = json.loads(order.product_info)
        quantity = order.dispatch_quantity or 0
        unitprice = order.unitprice + (order.unitprice * product_info['brand__stockist_margin'] / 100)
        price = quantity * unitprice
        cases, units = DistributorInvoice.get_cases_units(
            order.product.cld_configurations, quantity)

        shakti_orderline['distributor_order_detail'] = order.id
        shakti_orderline['product_name'] = order.product.basepack_name
        shakti_orderline['product_code'] = order.product.basepack_code
        shakti_orderline['product_size'] = " ".join(
            [order.product.basepack_size, order.product.unit.unit])

        
        shakti_orderline['product_mrp'] = product_info['mrp'] or order.product.mrp
        shakti_orderline['base_rate'] = unitprice
        shakti_orderline['product'] = order.product_id
        shakti_orderline['cases'] = cases
        shakti_orderline['units'] = units
        shakti_orderline['quantity'] = quantity
        shakti_orderline['unitprice'] = unitprice
        shakti_orderline['price'] = price
        shakti_orderline['cgstp'] = product_info['cgst']
        shakti_orderline['cgst'] = order.cgst
        shakti_orderline['sgstp'] = product_info['sgst']
        shakti_orderline['sgst'] = order.sgst
        shakti_orderline['igstp'] = product_info['igst']
        shakti_orderline['igst'] = order.igst
        shakti_orderline['cld_configuration'] = product_info['cld_configurations']
        
        shakti_orderline['discount'] = (
            order.discount_amount or 0) + (order.distributor_discount or 0)
        shakti_orderline['discount_amount'] = order.discount_amount or 0
        shakti_orderline['distributor_discount'] = order.distributor_discount or 0
        shakti_orderline['total_tax'] = order.cgst + order.sgst + order.igst
        gross_amount = price - \
            shakti_orderline['discount'] + shakti_orderline['total_tax']
        shakti_orderline['net_amount'] = round(gross_amount, 2)
        # shakti_orderline['net_amount'] = round(gross_amount +
        #                                        (gross_amount * product_info['brand__stockist_margin'] / 100), 2)

    @staticmethod
    def get_cases_units(cld_configuration, quantity):
        quotient_remainder = divmod(quantity, cld_configuration)
        return quotient_remainder[0], quotient_remainder[1]
