from django.core.management.base import BaseCommand, CommandError
from orders.models import AlliancePartnerOrder as ap
from orders.stock_management import StockManagement
from orders.lib.order_files import GenerateFile, StockCorrection, CancelOldOrders, ProcessPepsicoInvoice
from orders.lib.product_files import ProductFile
from orders.lib.rs_data import GstFile


class Command(BaseCommand):
    help = '''will place a primary order for Distributor \n
        user, "review" for place review order and "primary" for creating alliance order, \n
        "stockupdate" for updating distributor stock, \n
        "generatefile" for generating file for primary order.
    '''

    def add_arguments(self, parser):
        parser.add_argument('order_type', nargs='+', type=str)

    def handle(self, *args, **options):
        from orders.lib.create_distributor_order import CreateReviewOrder, CreatePrimaryOrder
        if 'review' in options['order_type']:
            obj = CreateReviewOrder()
            obj.generate_order()
        elif 'primary' in options['order_type']:
            obj = CreatePrimaryOrder()
            obj.generate_order()
        elif 'stockupdate' in options['order_type']:
            obj = StockManagement()
            obj.update_stocks()
        elif 'generatefile' in options['order_type']:
            obj = GenerateFile()
            obj.generate_file(['3964'])
        elif 'readfile' in options['order_type']:
            obj = GenerateFile()
            obj.process_files()
        elif 'readpepsicofile' in options['order_type']:
            obj = ProcessPepsicoInvoice()
            obj.process_pepsico_files()
        elif 'readproductfile' in options['order_type']:
            obj = ProductFile()
            obj.process_product_files()
        elif 'caltotalamount' in options['order_type']:
            obj = GenerateFile()
            obj.calculate_received_total(422)
        elif 'stockcorrection' in options['order_type']:
            obj = StockCorrection()
            obj.update_closing_stock()
        elif 'readrsgstfile' in options['order_type']:
            obj = GstFile()
            obj.process_gst_files()
        elif 'cancelorders' in options['order_type']:
            obj = CancelOldOrders()
            obj.cancel_orders()
        elif 'returnsoorders' in options['order_type']:
            obj = CancelOldOrders()
            date = None
            if len(options['order_type']) > 3:
                date = options['order_type'][3]
            order_ids = options['order_type'][2]
            distributor_id = options['order_type'][1]
            obj.return_so_orders(distributor_id, order_ids, date)
        else:
            raise CommandError(
                'Enter "review" | "primary" | stockupdate | generatefile | readfile as argument | readproductfile | caltotalamount | stockcorrection | readrsgstfile | cancelorders')

        # order_ids, distributor_ids =
        self.stdout.write(self.style.SUCCESS(
            'Successfully placed order %s' % (obj)))
