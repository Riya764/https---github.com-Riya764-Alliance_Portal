'''Custom field validations'''
from django.core.exceptions import ValidationError

def validate_image_100(self):
    '''validate image size'''
    if self.size > 100 * 1024:
        raise ValidationError("Image file too large ( > 100kb )")
    return True


def validate_product_image(self):
    '''validate image size'''
    if self.size > 300 * 1024:
        raise ValidationError("Image file too large ( > 300kb )")
    return True

def validate_spaces(self):
    '''validate field spaces'''
    if len(self.strip()) == 0:
        raise ValidationError("Please enter text.")
    return True

def validate_product_stocks(self):
    '''validate stock days'''
    if self > 730 or self < 30:
        raise ValidationError("Number of days to expiry with max limit of 730 and min of 30 days")
    return True
