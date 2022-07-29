'''order tags'''
import json
from django import template
from hul.choices import OrderStatus, PaymentStatus

from offers.models import PromotionLines

register = template.Library()


@register.simple_tag
def total_quantity(order_dict):
    """
    Method adding quantity of each product
    """
    quantity = 0
    for order in order_dict:
        quantity += order.quantity

    return quantity


@register.simple_tag
def total_amount(items):
    ''' caclulate sum of all items in a dict '''
    return sum(item.net_amount for item in items)


@register.simple_tag
def item_status_display(item):
    ''' display item status from code '''
    return OrderStatus.LABEL[item] if item else '-'


@register.simple_tag
def payment_status_display(item):
    ''' display item status from code '''
    return PaymentStatus.PAYMENTSLABEL[item]


@register.simple_tag
def json_loads(item):
    ''' display json loads data '''
    return json.loads(item)


@register.filter
def round_to_2(item):
    """
    format to 2 decimal places
    """

    return round(item or 0.0, 2)


@register.filter
def promotion_discount(promotion):
    ''' promotion discount from promotionline id '''
    promotions = []
    promotion_details = PromotionLines.objects.filter(
        id__in=promotion).values('discount')

    for promotion in promotion_details:
        promotions.append(str(promotion['discount']) + '%')
    return ', '.join(promotions)
