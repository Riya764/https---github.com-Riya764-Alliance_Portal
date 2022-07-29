''' job/models.py '''
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.encoding import python_2_unicode_compatible

from tinymce.models import HTMLField
from hul.choices import SentStatusType, OrderStatus
from hul.constants import FROM_EMAIL, ADMIN_EMAIL
from orders.models import DistributorOrder
# Create your models here.

@python_2_unicode_compatible
class Email(models.Model):
    '''Email Model'''
    from_email = models.CharField(
        max_length=255, default=FROM_EMAIL)
    to_email = models.EmailField(
        max_length=255, default=ADMIN_EMAIL, db_index=True)
    carbon_copy = ArrayField(models.EmailField(max_length=255),
                             blank=True, null=True, verbose_name='cc')
    subject = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    message = HTMLField()
    sent_status_type = models.IntegerField(choices=SentStatusType.STATUS, \
                        default=SentStatusType.PENDING)
    sent_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.to_email

@python_2_unicode_compatible
class MobileNotification(models.Model):
    ''' sending sms notification to users when order status is updated '''
    to_phone = models.CharField('Phone Number (Shakti)', max_length=15)
    distributor_order = models.ForeignKey(DistributorOrder)
    order_status = models.IntegerField(choices=OrderStatus.STATUS, db_index=True)
    message = HTMLField()
    sent_status_type = models.IntegerField(choices=SentStatusType.STATUS, \
                        default=SentStatusType.PENDING)
    sent_date = models.DateTimeField(null=True, blank=True)
    response_data = models.TextField(blank=True)

    def __str__(self):
        return self.to_phone
