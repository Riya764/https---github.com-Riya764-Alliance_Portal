''' orders/stock_management.py '''
import time
from pytz import timezone
from django.utils import timezone as dt
from django.db.models import Prefetch, Sum, Max
from django.db.models.functions import Coalesce

from orders.models import (AlliancePartnerOrderDetail, AlliancePartnerOrder,
                           DistributorStock, DistributorOrderDetail)
from product.models import Product
from hul.choices import OrderStatus
from django.core.mail.message import EmailMessage
from django.core.mail import send_mail
from hul.applogger import AppLogger


class StockManagement(object):

    debug_date = True

    def __init__(self):
        self.distributor_stock_details = {}
        self.prev_stock_date = DistributorStock.objects.filter().order_by(
            'created').last().created
        self.last_stock_date = self.prev_stock_date.astimezone(
            timezone('Asia/Kolkata')).date()
        self.date = dt.now().astimezone(timezone('Asia/Kolkata')).date()
        self.updated = []
        self.created = []

    def get_products(self):
        products = Product.objects.filter(
            is_active=True).select_related('brand')
        return products

    def create_distributor_stock(self, products):

        for product in products:
            distributors = product.brand.alliance_distributor_related.filter(
                is_active=True, user_id=32007).values()
            for distributor in distributors:
                distributor_id = distributor.get('user_id')
                product_id = product.pk

                if distributor_id not in self.distributor_stock_details:
                    self.distributor_stock_details[distributor_id] = {}

                if product_id not in self.distributor_stock_details[distributor_id]:
                    self.distributor_stock_details[distributor_id][product_id] = {
                    }

                    previous_qty = self.get_previous_quantity(
                        distributor_id, product_id
                    )
                    opening_stock = closing_stock = amount = 0
                    if previous_qty is not None:
                        opening_stock = previous_qty.opening_stock
                        closing_stock = previous_qty.closing_stock
                        amount = previous_qty.amount

                    self.distributor_stock_details[distributor_id][product_id].update(
                        {
                            'opening_stock': opening_stock,
                            'closing_stock': closing_stock,
                            'distributor': distributor_id,
                            'product': product_id,
                            'amount': amount
                        }
                    )
            self.set_opening_stock(product.distributorstock.filter(
                created__date=self.last_stock_date))

        if self.distributor_stock_details:
            self.save_distributor_stocks()

    @staticmethod
    def get_previous_quantity(distributor_id, product_id):
        return DistributorStock.objects.filter(
            distributor_id=distributor_id, product_id=product_id
        ).order_by('-created').first()

    def set_opening_stock(self, distributor_stocks):
        '''
        set opening stock
        begining of day, update opening stock to previous day's closing stock        
        '''
        if distributor_stocks:
            # update opening stock from yesterday's closing stock
            for stock in distributor_stocks:
                distributor_id = stock.distributor_id
                product_id = stock.product_id
                yesterday_closing = stock.closing_stock
                try:
                    self.distributor_stock_details[distributor_id][product_id].update(
                        {
                            'opening_stock': yesterday_closing,
                            'closing_stock': yesterday_closing,
                            'amount': yesterday_closing * stock.product.tur
                        }
                    )
                except:
                    pass

    def save_distributor_stocks(self):
        ''' save distributor stocks '''
        stock_details = self.distributor_stock_details.values()

        for detail in stock_details:
            for dic in detail.values():
                obj, created = DistributorStock.objects.get_or_create(
                    defaults={
                        'product_id': dic['product'],
                        'distributor_id': dic['distributor'],
                        'opening_stock': dic['opening_stock'],
                        'closing_stock': dic['closing_stock'],
                        'amount': dic['amount'],
                        'created': dt.now(),
                        'modified': dt.now()
                    },
                    product_id=dic['product'],
                    distributor_id=dic['distributor'],
                    created__date=self.date
                )

                if created:
                    self.created.append(str(obj.id))
                else:
                    self.updated.append(str(obj.id))

        if self.debug_date:
            self.debug_current_date()

    def update_stocks(self):
        products = self.get_products()
        self.create_distributor_stock(products)

    def debug_current_date(self):
        subject = 'HUL CRON - debug date'

        html_content = '''
        Current date: {}
        Last stock date: {}
        created records: {}\n
        udpated records: {}
        '''.format(self.date.strftime('%Y-%m-%d'), self.last_stock_date.strftime('%Y-%m-%d'), ', '.join(self.created), ', '.join(self.updated))

        msg = send_mail(subject,
                        html_content,
                        'no-reply@ishaktiapp.com',
                        ['Shrishchandra.shukla@simtechitsolutions.in', 'raghavendran.m@simtechitsolutions.in'], fail_silently=True)
        # msg.send()

    def update_stocks_specific_date(self):

        distributor_stocks = DistributorStock.objects.filter(created__date='2019-11-26', distributor_id__in=[
                                                             '3232', '3235', '3254', '3205', '3242', '3256', '3173', '3240', '3177', '3179', '3272', '3184', '3251', '3267', '3208', '3262', '3268', '3191'])
        prev_date = '2019-11-22'
        i = 0
        for stock in distributor_stocks:
            print('Todays', stock.created.date(), stock.distributor.name,
                  stock.product, stock.opening_stock, stock.closing_stock)
            if stock.closing_stock == 0:
                previous_stock = DistributorStock.objects.filter(
                    created__date=prev_date, distributor_id=stock.distributor_id, product_id=stock.product_id).get()
                # import pdb ; pdb.set_trace()
                print('previous day', previous_stock.created.date(), previous_stock.distributor.name,
                      previous_stock.product, previous_stock.opening_stock, previous_stock.closing_stock)
                stock.opening_stock = previous_stock.opening_stock
                stock.closing_stock = previous_stock.closing_stock
                stock.amount = previous_stock.amount
                stock.modified = stock.modified
                stock.save()
            print('updated', stock.created.date(), stock.distributor.name,
                  stock.product, stock.opening_stock, stock.closing_stock)
            i += 1

        print(i)

    def create_stock_logs(self, distributor_id):

        present_stock = {}
        received_stock = {}
        d_stock_present = DistributorStock.objects.filter(
            created__date=dt.now().date(), distributor_id__in=distributor_id)
        for p_stock in d_stock_present:
            present_stock.update(
                {
                    'created': p_stock.created.date(),
                    'distibutor_id': p_stock.distributor.id,
                    'distributor_name': p_stock.distributor.name,
                    'product_id': p_stock.product,
                    'product_name': p_stock.product.basepack_name,
                    'opening_stock': p_stock.opening_stock,
                    'closing_stock': p_stock.closing_stock
                }
            )
            app_logger_obj = AppLogger()
            app_logger_obj.info_log(
                'Present Distributor Stock Details', present_stock)
        a_date = AlliancePartnerOrder.objects.filter(
            distributor_id__in=distributor_id, order_status=OrderStatus.RECEIVED).aggregate(Max('created'))
        d_stock_received = DistributorStock.objects.filter(
            created__date=a_date['created__max'].date(), distributor_id__in=distributor_id)
        for d_stock in d_stock_received:
            received_stock.update(
                {
                    'created': d_stock.created.date(),
                    'distibutor_id': d_stock.distributor,
                    'distributor_name': d_stock.distributor.name,
                    'product_id': d_stock.product.id,
                    'product_name': d_stock.product.basepack_name,
                    'opening_stock': d_stock.opening_stock,
                    'closing_stock': d_stock.closing_stock
                }
            )
            app_logger_obj = AppLogger()
            app_logger_obj.info_log(
                'Received Distributor Stock Details', received_stock)

        return received_stock
