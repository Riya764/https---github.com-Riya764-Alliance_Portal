'''pdf filters'''
import urllib
import cStringIO
import base64
from django import template

from offers.models import PromotionLines

register = template.Library()


@register.filter
def get64(url):
    """
    Method returning base64 image data instead of URL
    """
    if url.startswith("http"):
        image = cStringIO.StringIO(urllib.urlopen(url).read())
        return 'data:image/jpg;base64,' + base64.b64encode(image.read())

    return url

@register.filter
def get_order_total(qs):
    """
    Method returning total price for mutiple Pidilite invoice
    """
    total = 0
    for item in qs:
        total += item.net_amount
    return total


@register.filter
def calculate_tcs(amount):
    """
    Method to calculate TCS
    """
    tcs = round(amount * 0.1 / 100, ndigits=2)
    return tcs


@register.filter
def calculate_final_amount(amount):
    """
    Add TCS to Amount
    """
    tcs = round(amount * 0.1 / 100, ndigits=2)

    return amount + tcs

@register.filter
def sum_invoice(qs, field):
    """
    To get sum of Allianceorderdetails table items
    """
    total = 0
    for item in qs:
        value = getattr(item, field)
        total += value
    return total


@register.filter
def pescio_final_amount(qs, field):
    """
    To get sum of Allianceorderdetails table items
    """
    total = 0
    for item in qs:
        value = getattr(item, field)
        total += value
    tcs = round(total * 0.1 / 100, ndigits=2)
    return total + tcs
