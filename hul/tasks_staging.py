''' hul/tasks.py scheduling tasks run by celery '''
import os
import sys
from datetime import datetime

import django
from django.core.mail.message import EmailMessage
from django.utils import timezone

import boto3
from celery import Celery

from hul.choices import SentStatusType
from hul.settings.common import SNS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from hul.constants import HTTP_STATUSCODE
from job.models import Email, MobileNotification


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'hul.settings.staging'
django.setup()

CELERYAPP = Celery('hul.celery')

@CELERYAPP.task(name="hul.tasks.schedular_of_email")
def shedular_of_email():
    '''Schedular to send Emals'''
    email_set = Email.objects.filter(
        sent_status_type=SentStatusType.PENDING)
    for email in email_set:
        try:
            from_email = email.from_email
            to_email = email.to_email
            html_content = email.message
            subject = email.subject
            lst_cc_email = email.cc

            msg = EmailMessage(
                subject, html_content, from_email, [to_email], carbon_copy=lst_cc_email)
			# Main content is now text/html
            msg.content_subtype = "html"
            sent_status = msg.send()
            if int(sent_status) == 1:
                email.sent_status_type = SentStatusType.SUCCESS
                email.sent_date = datetime.now()
                email.save()
            elif int(sent_status) == 0:
                email.sent_status_type = SentStatusType.ERROR
                email.send_date = datetime.now()
                email.save()
        except StandardError:
            email.sent_status_type = SentStatusType.PENDING
            email.save()

@CELERYAPP.task(name="hul.tasks.schedular_of_sms")
def shedular_of_sms():
    '''Schedular to send SMS'''
    sms_set = MobileNotification.objects.filter(
        sent_status_type=SentStatusType.PENDING)
    sns = boto3.client('sns',
                       aws_access_key_id=AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                       region_name=SNS_REGION)

    for sms in sms_set:
        try:
            to_phone = sms.to_phone
            message = sms.message
            sent_status = sns.publish(PhoneNumber=to_phone, Message=message)

            if sent_status['ResponseMetadata']['HTTPStatusCode'] == HTTP_STATUSCODE:
                sms.sent_status_type = SentStatusType.SUCCESS
                sms.sent_date = timezone.now()
                sms.response_data = sent_status['ResponseMetadata']
                sms.save()
            else:
                sms.sent_status_type = SentStatusType.ERROR
                sms.send_date = timezone.now()
                sms.response_data = sent_status['ResponseMetadata']
                sms.save()
        except StandardError:
            sms.sent_status_type = SentStatusType.PENDING
            sms.response_data = sent_status['ResponseMetadata']
            sms.save()
