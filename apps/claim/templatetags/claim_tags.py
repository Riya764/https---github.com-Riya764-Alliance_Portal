'''claim/claim_tags.py'''
from django import template
from hul.choices import ClaimStatus

register = template.Library()


@register.simple_tag
def total_discount(items, bonus):
    ''' caclulate sum of all items in a dict '''
    product_sum = sum(item['discount_amount'] for item in items)
    bonus_sum = sum(item.discount_amount for item in bonus)
    return product_sum + bonus_sum or 0


@register.simple_tag
def total_ordered(items):
    ''' caclulate sum of all items in a dict '''
    return sum(item['ordered_amount'] for item in items)


@register.simple_tag
def claimstatus_label(item):
    ''' return label of claim status '''
    label = ''
    if item:
        label = ClaimStatus.LABEL[item]
    return label
