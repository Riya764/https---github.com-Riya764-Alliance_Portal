'''
models for logs
'''
from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
# Create your models here.

@python_2_unicode_compatible
class Log(models.Model):
    '''
    log model
    '''
    remote_address = models.CharField(null=True, blank=True, max_length=255)
    user_email = models.CharField(null=True, blank=True, max_length=255)
    method_type = models.CharField(null=True, blank=True, max_length=255)
    method_name = models.CharField(null=True, blank=True, max_length=255)
    access_token = models.CharField(null=True, blank=True, max_length=350)

    request_content_length = models.CharField(
        null=True, blank=True, max_length=255,
        verbose_name="Request size in Kilobyte.")
    request_content = models.TextField(null=True, blank=True)
    request_datetime = models.DateTimeField(blank=True, null=True)

    response_status_type = models.CharField(
        null=True, blank=True, max_length=255)
    response_content = models.TextField(null=True, blank=True)
    response_content_length = models.CharField(
        null=True, blank=True, max_length=255,
        verbose_name="Response size in Kilobyte.")
    response_datetime = models.DateTimeField(blank=True, null=True)

    total_time_taken = models.FloatField(null=True, blank=True)
    extra_log = models.TextField(null=True, blank=True)

    exception_full_stack_trace = models.TextField(null=True, blank=True)
    exception_short_value = models.CharField(
        null=True, blank=True, max_length=255)

    def __str__(self):
        return self.remote_address

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.request_datetime = timezone.now()
        self.response_datetime = timezone.now()
        return super(Log, self).save(*args, **kwargs)

    @property
    def short_request_content(self):
        '''
        short request content
        '''
        return truncatechars(self.request_content, 100)

    @property
    def short_response_content(self):
        '''
        short response content
        '''
        return truncatechars(self.response_content, 100)

    @property
    def full_stack_trace(self):
        '''
        short exception full stack trace
        '''
        return truncatechars(self.exception_full_stack_trace, 100)
