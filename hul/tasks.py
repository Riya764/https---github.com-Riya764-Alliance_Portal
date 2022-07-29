''' hul/tasks.py scheduling tasks run by celery '''
import os
import sys
from datetime import datetime

import django
import time
from django.core.mail.message import EmailMessage
from django.utils import timezone
from django.conf import settings

import boto3
# from celery import task
from hul.celery import app as celery_app

from hul.choices import SentStatusType
from hul.constants import HTTP_STATUSCODE
try:
    from job.models import Email, MobileNotification
    from moc.lib.create_moc import CreateMoC
    from orders.stock_management import StockManagement
    from orders.lib.create_distributor_order import CreateReviewOrder, CreatePrimaryOrder
    from orders.lib.order_files import GenerateFile, CancelOldOrders
    from orders.lib.product_files import ProductFile
except Exception:
    from apps.job.models import Email, MobileNotification
    from apps.moc.lib.create_moc import CreateMoC
    from apps.orders.stock_management import StockManagement
    from apps.orders.lib.create_distributor_order import CreateReviewOrder, CreatePrimaryOrder
    from apps.orders.lib.order_files import GenerateFile, CancelOldOrders
    from apps.orders.lib.product_files import ProductFile


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

django.setup()

# CELERYAPP = Celery('hul')

# CELERYAPP.config_from_object('django.conf:settings')

FROM_EMAIL = settings.EMAIL_DEFAULT
DEBUG_EMAIL = settings.ADMINS[1][1]


@celery_app.task(name="hul.tasks.test_job")
def test_job():
    '''Schedular to send Emals'''
    print("test job completed")


@celery_app.task(name="hul.tasks.schedular_of_email")
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
                subject, html_content, from_email, [to_email], cc=lst_cc_email)
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


@celery_app.task(name="hul.tasks.schedular_of_sms")
def shedular_of_sms():
    '''Schedular to send SMS'''
    sms_set = MobileNotification.objects.filter(
        sent_status_type=SentStatusType.PENDING)
    sns = boto3.client('sns',
                       aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                       aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                       region_name=settings.SNS_REGION)

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


@celery_app.task(name="hul.tasks.test_email")
def send_test_email():
    ''' send email'''
    from_email = settings.EMAIL_DEFAULT
    to_email = settings.ADMINS[0][1]
    html_content = 'test message'
    subject = 'test subject'
    lst_cc_email = []

    msg = EmailMessage(
        subject, html_content, from_email, [to_email], cc=lst_cc_email)
    # Main content is now text/html
    msg.content_subtype = "html"
    try:
        msg.send()
    except StandardError as e:
        print(e.message)


@celery_app.task(name="hul.tasks.stock_update")
def update_distributor_stock():
    ''' update distributor stock '''
    s1 = time.time()
    stock_obj = StockManagement()
    subject = 'HUL CRON - Stock Update cron'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    lst_cc_email = []
    try:
        stock_obj.update_stocks()
        s2 = time.time()
        process_time = s2 - s1
        html_content = '''
            stock updated successfully in {process_time}
            '''.format(process_time=process_time)
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email],
                       cc=lst_cc_email)
    # Main content is now text/html
    msg.content_subtype = "html"
    try:
        print(html_content)
    except StandardError as e:
        print(e.message)


@celery_app.task(name="hul.tasks.create_review_order")
def create_review_order():
    ''' create distributor review order '''
    s1 = time.time()
    order_obj = CreateReviewOrder()
    subject = 'huL- create review order cron'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    lst_cc_email = []
    try:
        order_obj.generate_order()
        s2 = time.time()
        process_time = s2 - s1
        html_content = '''
            review order(s) successfully created in {process_time}
            '''.format(process_time=process_time)
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email],
                       cc=lst_cc_email)
    # Main content is now text/html
    msg.content_subtype = "html"
    try:
        msg.send()
    except StandardError as e:
        print(e.message)


@celery_app.task(name="hul.tasks.create_primary_order")
def create_primary_order():
    ''' create alliance order '''
    s1 = time.time()
    order_obj = CreatePrimaryOrder()
    subject = 'huL- create primary order cron'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    lst_cc_email = []
    try:
        order_obj.generate_order()
        s2 = time.time()
        process_time = s2 - s1
        html_content = '''
            review order(s) successfully created in {process_time}
            '''.format(process_time=process_time)
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email],
                       cc=lst_cc_email)
    # Main content is now text/html
    msg.content_subtype = "html"
    try:
        msg.send()
    except StandardError as e:
        print(e.message)


@celery_app.task
def generate_file(review_order_id):
    '''
    generate file
    '''
    subject = 'HUL CRON - generate file'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    try:
        file_obj = GenerateFile()
        file_obj.generate_file(review_order_id)
        html_content = "File for order {} generated successfully".format(
            review_order_id)
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email])
    msg.send()


@celery_app.task(name="hul.tasks.read_order_file", bind=True, max_retries=3)
def read_order_files(self):
    '''
    read order files
    '''
    subject = 'HUL CRON - process file'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    try:
        file_obj = GenerateFile()
        file_obj.process_files()
        html_content = "Order files processed successfully"
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email])
    msg.send()


@celery_app.task(name="hul.tasks.read_product_file", bind=True, max_retries=3)
def read_product_files(self):
    '''
    read product files
    '''
    subject = 'HUL CRON - process product file'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    try:
        file_obj = ProductFile()
        file_obj.process_product_files()
        html_content = "Product file processed successfully"
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email])
    msg.send()


@celery_app.task(name="hul.tasks.create_moc", bind=True, max_retries=3)
def create_moc(self, year):
    CreateMoC.create_moc_year(year)


@celery_app.task(name="hul.tasks.cancel_old_orders", bind=True, max_retries=3)
def cancel_old_orders(self):
    '''
    cancel 30 days old primary orders 
    '''
    subject = 'HUL CRON - process product file'
    from_email = FROM_EMAIL
    to_email = DEBUG_EMAIL
    try:
        file_obj = CancelOldOrders()
        file_obj.cancel_orders()
        html_content = "Orders Cancelled successfully"
    except StandardError as e:
        html_content = e.message

    msg = EmailMessage(subject,
                       html_content,
                       from_email,
                       [to_email])
    msg.send()
