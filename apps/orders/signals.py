''' orders/signals/handlers.py '''
import datetime
import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.context import Context
from django.utils import timezone
from django.conf import settings

from moc.models import MoCMonth

from orders.lib.order_management import OrderManagement
from orders.models import (DistributorOrder, DistributorOrderDetail, DistributorStock,
                           AlliancePartnerOrder, AlliancePartnerOrderDetail)

from hul.choices import OrderStatus

# Get an instance of a logger
logger = logging.getLogger(__name__)


@receiver(post_save, sender=DistributorOrder, dispatch_uid="update_distributor_order_status")
def send_distributor_order_status(sender, instance, **kwargs):
    ''' sending email notification to user when order status is updated '''
    #order_mgm_obj = OrderManagement()
    #invoice_number = order_mgm_obj.prepare_rsp_order_id(instance.id)
    invoice_number =instance.invoice_number
    email_data = {}

    order_status = instance.get_order_status_display()
    email_data['order_status'] = order_status
    email_data['payment_status'] = instance.payment_status
    email_data['distributor_order_id'] = instance.id

    if kwargs['created']:
        instance.invoice_number = invoice_number
        instance.save()
        # send email rd that a new order has been placed by RSP
        if instance.order_status == OrderStatus.ORDERED:
            email_data['to_email'] = instance.distributor.email
            context = Context({
                'name': instance.distributor.name,
                'order_id': invoice_number,
                'total_amount': instance.total_amount,
                'order_date': instance.created,
                'order_status': order_status,
                'by_name': instance.sales_promoter.name
            })

    elif not kwargs['created']:
        if instance.order_status == OrderStatus.DISPATCHED and instance.moc is None:
            moc = MoCMonth.objects.filter(start_date__lte=instance.created.date(), end_date__gte=instance.created.date()).first()
            instance.moc = moc
            instance.save()

        email_data['to_email'] = instance.sales_promoter.email
        email_data['to_phone'] = instance.shakti_enterpreneur.contact_number

        context = Context({
            'name': instance.sales_promoter.name,
            'order_id': invoice_number,
            'total_amount': instance.total_amount,
            'order_date': instance.created,
            'by_name': instance.distributor.name,
            'order_status': order_status,
            'current_date': datetime.datetime.now()
        })

    try:
        filepath = order_mgm_obj.send_email_notification(context, email_data)

    except StandardError:
        logger.error(StandardError)

    if 'to_phone' in email_data and \
       instance.order_status in [OrderStatus.DISPATCHED, OrderStatus.CONFIRMED]:
        try:
            email_data['order_status'] = instance.order_status
            order_mgm_obj.send_sms_notification(context, email_data)
        except StandardError:
            logger.error(StandardError)


@receiver(post_save, sender=AlliancePartnerOrder, dispatch_uid="update_alliance_order_status")
def send_alliance_order_status(sender, instance, **kwargs):
    ''' sending email notification to user when order status is updated '''

    order_mgm_obj = OrderManagement()

    email_data = {}
    order_status = instance.get_order_status_display()
    email_data['order_status'] = order_status
    email_data['payment_status'] = instance.payment_status
    if kwargs['created']:
        try:
            prev_order = instance.get_previous_by_created(
                distributor_id=instance.distributor_id)
            prev_order_id = prev_order.order_id or 0
            instance.order_id = prev_order_id + 1
        except instance.DoesNotExist:
            instance.order_id = 1
        moc = MoCMonth.objects.filter(
            start_date__lte=instance.created.date(), end_date__gte=instance.created).first()
        instance.moc = moc
        order_id = order_mgm_obj.prepare_alliance_order_id(
            instance.order_id, instance.alliance_code)
        instance.invoice_number = order_id
        instance.save()

    elif not kwargs['created']:
        email_data['to_email'] = instance.distributor.email

        context = Context({
            'name': instance.distributor.name,
            'order_id': instance.invoice_number,
            'total_amount': instance.total_amount,
            'order_date': instance.created,
            'by_name': instance.alliance.name,
            'order_status': order_status,
            'current_date': timezone.now()
        })

        if settings.ORDER_EMAIL_NOTIFICATION:
            try:
                order_mgm_obj.send_email_notification(context, email_data)
            except StandardError:
                logger.error(StandardError)


#@receiver(post_save, sender=AlliancePartnerOrderDetail,
#          dispatch_uid="update_distributor_order_detail_status")
def update_distributor_detail(sender, instance, **kwargs):
    '''
    update order status of Distributor order details table
    '''
    if settings.PIDILITE['FTP_ORDER_FILE']:
        '''
        new columns in RS: dist_channel, division, customer_code, plant
        '''
        file_data = {
            'order_id': instance.id,
            'mat_code': instance.product.basepack_code,
            'cust_code': instance.alliance_partner_order.distributor.regionaldistributor.ap_code,
            'dist_channel': instance.alliance_partner_order.distributor.regionaldistributor.ap_dist_channel,
            'division': instance.alliance_partner_order.distributor.regionaldistributor.ap_division,
            'order_qty': instance.quantity,
            'cld_config': instance.product.cld_configurations,
            'plant': instance.alliance_partner_order.distributor.regionaldistributor.ap_plant,
            'order_date': instance.created

        }
        # parsexmlobj = ParseXml()

        # try:
        #     filepath = parsexmlobj.create_xml(file_data)
        #     # transfer file to remote location
        #     ftpobj = TransferFile()
        #     con = ftpobj.connect_ftp()
        #     try:
        #         ftpobj.upload_file(con, filepath)
        #     except StandardError:
        #         logger.error(StandardError)

        # except StandardError:
        #     raise "Could not write xml file"
        #     logger.error('Could not write xml file for order id: %s')

    try:
        distributor_order_detail_id = instance.distributor_order_detail_id
        alliance_item_status = instance.item_status

        if OrderStatus.DELIVERED == alliance_item_status:
            alliance_item_status = OrderStatus.READYPICKUP
        if OrderStatus.ORDERED == alliance_item_status:
            alliance_item_status = OrderStatus.CONFIRMED
        if OrderStatus.DISPATCHED == alliance_item_status:
            alliance_item_status = OrderStatus.SHIPPED

        do_detail_obj = DistributorOrderDetail.objects.filter(
            pk=distributor_order_detail_id).first()
        do_detail_obj.item_status = alliance_item_status
        do_detail_obj.save()

        do_other_details = do_detail_obj.distributor_order.distributor_order_details.values()

        do_other_status_list = []
        for do_other_detail in do_other_details:
            do_other_status_list.append(do_other_detail['item_status'])
        unique_status = set(do_other_status_list)

        if len(unique_status) == 1:
            DistributorOrder.objects.filter(pk=do_detail_obj.distributor_order_id).update(
                order_status=alliance_item_status)
    except StandardError:
        logger.error(StandardError)


@receiver(post_save, sender=DistributorOrderDetail, dispatch_uid="update_distribtor_stock1")
@receiver(post_save, sender=AlliancePartnerOrderDetail, dispatch_uid="update_distribtor_stock2")
def update_distribtor_stock(sender, instance, **kwargs):
    try:
        product = instance.product
        distributor = instance.alliance_partner_order.distributor if hasattr(instance, "alliance_partner_order") else \
            instance.distributor_order.distributor

        distributor_product_stock = DistributorStock.objects.filter(
            product=product, distributor=distributor
        ).order_by('-created').first()
        
        quantity = instance.dispatch_quantity if instance.dispatch_quantity is not None else instance.quantity
        if instance.item_status in [OrderStatus.RECEIVED, OrderStatus.RETURNED]:
            distributor_product_stock.closing_stock += quantity

        if instance.item_status == OrderStatus.DISPATCHED and distributor_product_stock.closing_stock >= quantity:
            distributor_product_stock.closing_stock -= quantity
        
        distributor_product_stock.amount = distributor_product_stock.closing_stock * distributor_product_stock.product.tur
        distributor_product_stock.save()
    except AttributeError:
        DistributorStock.objects.create(product=product, distributor=distributor)
        pass
    except e as Exception:
        print(e)