'''
orders/lib/order_files.py
'''

import tablib
import os
import errno
from datetime import datetime, timedelta
from os.path import join
from django.utils import timezone as dt
from django.conf import settings
from django.db.models import Sum, F, Q
from orders.models import AlliancePartnerOrderDetail, DistributorOrder, AlliancePartnerOrder, DistributorOrderDetail, DistributorStock
from app.models import User
from product.models import Product, ProductChild
from orders.lib.order_management import CalculatePrice
from hul.choices import OrderStatus
from django.core.mail import send_mail
import logging
import paramiko

# Get an instance of a logger
logger = logging.getLogger(__name__)


class GenerateFile(object):
    '''
    generate primary order xls files
    '''
    UOM = {
        'DR': 'DR',
        'CV': 'CV',
        'CS': 'CS',
        'EA': 'EA'
    }

    FLAG = {
        'S': OrderStatus.INTRANSIT,
        'E': OrderStatus.CANCELLED,
    }

    def _get_order_detail(self, order_ids):
        order_details = AlliancePartnerOrderDetail.objects.filter(
            alliance_partner_order__in=order_ids).select_related('alliance_partner_order')
        return order_details

    def generate_file(self, primary_orders):
        '''
        xls file will be generated in tmp folder for the order to be placed
        '''
        order_details = self._get_order_detail(primary_orders)
        pidilte_orders = []
        pepsico_orders = []
        for order in order_details:
            code = order.alliance_partner_order.alliance.alliancepartner.code
            if int(code) == 1001:
                pidilte_orders.append(order)
            if int(code) == 1003:
                pepsico_orders.append(order)
        if pepsico_orders:
            self._generate_pepsico_file(pepsico_orders)
        if pidilte_orders:
            self._generate_pidilite_file(pidilte_orders)

    def _generate_pepsico_file(self, order_details):
        print("Generating Pepsico order file")
        data = tablib.Dataset()
        data.headers = ['PO_No', 'PO_Date', 'Cust_Code', 'Hul_Code', 'En_code', 'Mat_Code', 'Order_Qty', 'UOM_Desc', 'Plant',
                        'ShipToAddress'
                        ]
        for order in order_details:
            cust_code = order.alliance_partner_order.distributor.regionaldistributor.code
            hul_code = order.alliance_partner_order.distributor.regionaldistributor.hul_code
            cust_code_pad = str(cust_code).zfill(10)
            today = dt.now().strftime('%Y%m%d')
            po_no = '{cust_code}/P/{cust_code_pad}/H/{serial}'.format(
                cust_code=cust_code, cust_code_pad=cust_code_pad, serial=order.alliance_partner_order.order_id)
            data.append([po_no,
                         today,
                         cust_code_pad,
                         hul_code,
                         order.product.en_code,
                         order.product.basepack_code,
                         order.quantity,
                         self.UOM['EA'],
                         order.alliance_partner_order.distributor.regionaldistributor.ap_plant,
                         cust_code_pad,
                         ])
            

        tmp_path = settings.PEPSICO['TMP']

        filename = "In_AllianceOrderDetails_Pepsico_{0}.xls".format(
            dt.now().strftime('%Y%m%d%H%M%S'))
        filepath = join(tmp_path, filename)
        print(filepath)

        with open(filepath, 'wb') as f:
            f.write(data.export('xls'))

        sftp = SFTPConnection()
        sftp.connect(settings.PEPSICO['HOST'], settings.PEPSICO['USER'],
                     pkey=settings.PEPSICO['PKEY_PATH'], passpharse=settings.PEPSICO['PKEY_PASSWORD'])
        sftp.upload(filepath, settings.PEPSICO['INBOUND'] + filename)
        sftp.close()

    def _generate_pidilite_file(self, order_details):
        print("Generating Pidilite order file")
        data = tablib.Dataset()
        data.headers = ['PO_No', 'PO_Date', 'PO_Type', 'Order_Type', 'Sales_Org', 'Dist_Channel',
                        'Division', 'Cust_Code', 'Mat_Code', 'Order_Qty', 'UOM_Desc', 'Plant',
                        'ShipToAddress', 'wssvalue', 'custremark', 'transportremark', 'prdscheduledate'
                        ]
        for order in order_details:
            cust_code = order.alliance_partner_order.distributor.regionaldistributor.code
            cust_code_pad = str(cust_code).zfill(10)
            today = dt.now().strftime('%Y%m%d')
            po_type = '0002'
            order_type = 'ZDDS'
            sales_org = '1000'

            cases, units = divmod(
                order.quantity, order.product.cld_configurations)

            if units > 0:
                order_qty = str(units)
                uom_desc = self.UOM['DR']
            elif units == 0 and cases > 0:
                order_qty = str(cases)
                uom_desc = self.UOM['CV']

            po_no = '{cust_code}/P/{cust_code_pad}/H/{serial}'.format(
                cust_code=cust_code, cust_code_pad=cust_code_pad, serial=order.alliance_partner_order.order_id)

            data.append([po_no,
                         today,
                         po_type,
                         order_type,
                         sales_org,
                         order.alliance_partner_order.distributor.regionaldistributor.ap_dist_channel,
                         order.alliance_partner_order.distributor.regionaldistributor.ap_division,
                         cust_code_pad,
                         order.product.basepack_code,
                         order_qty,
                         uom_desc,
                         order.alliance_partner_order.distributor.regionaldistributor.ap_plant,
                         cust_code_pad,
                         0,  # wssvalue
                         '',  # custremark
                         '',  # transportremark
                         ''  # prdscheduledate
                         ])

        tmp_path = settings.PIDILITE['TMP']
        filename = "In_AutoAndPushWSS{0}.xls".format(
            dt.now().strftime('%Y%m%d%H%M%S'))
        filepath = join(settings.TMP_ROOT, filename)
        print(filepath)

        with open(filepath, 'wb') as f:
            f.write(data.export('xls'))

        # ftp_obj = FTPOrderFile()
        # ftp_obj.upload_file(filepath, filename)

    def process_files(self):
        # ftp_obj = FTPOrderFile()
        # filenames = ftp_obj.get_files()
        filenames = ["RB_Autopo_Invoice_12062022.csv", ]
        for filename in filenames:
            filepath = join(settings.TMP_ROOT, filename)
            try:
                if 'out_autoandpushwssporesult' in filename.lower():
                    # status file update
                    self._update_status_data(filepath)
                elif 'rb_autopo_invoice' in filename.lower():
                    # quantity/discount update
                    self._process_data(filepath)
            except Exception as e:
                logger.error(e)
                print(e)
                pass

            # self._remove_file(filepath)

    def _update_status_data(self, filename):
        '''
        get alliance order detail object and update status of the order
        from order file
        '''

        dataset = tablib.Dataset()
        dataset.csv = open(filename, 'rb').read()
        # price_obj = CalculatePrice()
        # alliance_order_list = []
        alliance_partner_order = {}
        for row in dataset:
            po_no = row[1].split('/')
            alliance_order_id = po_no[-1]
            distributor_code = po_no[0]
            basepack_code = row[8]
            # uom = row[10]
            order_inst = AlliancePartnerOrderDetail.objects.select_related(
                'alliance_partner_order', 'product').filter(
                alliance_partner_order__order_id=alliance_order_id,
                product__basepack_code=basepack_code,
                alliance_partner_order__distributor__regionaldistributor__code=distributor_code).first()

            if not order_inst:
                basepack_code = ProductChild.objects.filter(
                    child_basepack_code=row[8]).first().mother_basepack_code.basepack_code
                order_inst = AlliancePartnerOrderDetail.objects.select_related(
                    'alliance_partner_order', 'product').filter(
                    alliance_partner_order__order_id=alliance_order_id,
                    product__basepack_code=basepack_code,
                    alliance_partner_order__distributor__regionaldistributor__code=distributor_code).first()

            alliance_partner_order_id = order_inst.alliance_partner_order_id
            # cld = order_inst.product.cld_configurations
            # dispatch_quantity = order_inst.dispatch_quantity + int(float(row[9])) or 0

            if row[12] is None:
                continue

            flag = row[12].upper()
            # if uom in [self.UOM['CS'], self.UOM['CV']]:
            #     dispatch_quantity = dispatch_quantity * cld

            # status = self.FLAG[flag]

            # taxable_amount = order_inst.unitprice

            # taxes = {'cgst': order_inst.cgst,
            #          'sgst': order_inst.sgst, 'igst': order_inst.igst}

            # cal_price_obj = CalculatePrice()
            # order_inst.dispatch_quantity = dispatch_quantity
            # order_inst.dispatched_on = dt.now()
            # net_amount, cgst, sgst, igst = cal_price_obj.calculate_tax(
            #     taxable_amount, **taxes)
            # order_inst.cgst_amount = cgst
            # order_inst.sgst_amount = sgst
            # order_inst.igst_amount = igst
            # order_inst.price = taxable_amount
            order_inst.item_status = self.FLAG[flag] if flag == 'E' else order_inst.item_status
            order_inst.save()

            if alliance_partner_order_id not in alliance_partner_order:
                pass
                # alliance_partner_order[alliance_partner_order_id] = {}
                # alliance_partner_order[alliance_partner_order_id]['total_amount'] = 0
                # alliance_partner_order[alliance_partner_order_id]['order_amount'] = 0
                # alliance_partner_order[alliance_partner_order_id]['tax'] = 0
                # alliance_partner_order[alliance_partner_order_id]['order_id'] = alliance_partner_order_id

            # alliance_partner_order[alliance_partner_order_id]['order_amount'] += float(
            #     order_inst.price)
            # alliance_partner_order[alliance_partner_order_id]['tax'] += cgst + sgst + igst
            # alliance_partner_order[alliance_partner_order_id]['total_amount'] += net_amount

        # for order in alliance_partner_order.values():
        #     AlliancePartnerOrder.objects.filter(pk=order['order_id']).update(
        #         order_status=OrderStatus.INTRANSIT)

    def _process_data(self, filename):
        '''
        get alliance order detail object and update dispatched quantity,
        dispatched date time and value from invoice file
        '''
        dataset = tablib.Dataset()
        dataset.csv = open(filename, 'rb').read()
        alliance_partner_order = {}
        basepack_obj = {}
        order_ids = []

        for row in dataset:
            invoice_number_alliance = str(row[0])
            po_no = row[7].split('/')
            alliance_order_id = po_no[-1]
            distributor_code = po_no[0]
            basepack_code = row[9]

            order_inst = AlliancePartnerOrderDetail.objects.select_related(
                'alliance_partner_order', 'product').filter(
                alliance_partner_order__order_id=alliance_order_id,
                product__basepack_code=basepack_code,
                alliance_partner_order__distributor__regionaldistributor__code=distributor_code, item_status=OrderStatus.ORDERED).first()
            try:
                if not order_inst:
                    basepack_code = ProductChild.objects.filter(
                        child_basepack_code=row[9]).first().mother_basepack_code.basepack_code
                    order_inst = AlliancePartnerOrderDetail.objects.select_related(
                        'alliance_partner_order', 'product').filter(
                        alliance_partner_order__order_id=alliance_order_id,
                        product__basepack_code=basepack_code,
                        alliance_partner_order__distributor__regionaldistributor__code=distributor_code, item_status=OrderStatus.ORDERED).first()
            except AttributeError as e:
                pass

            if not order_inst:
                order_inst = AlliancePartnerOrderDetail.objects.select_related(
                    'alliance_partner_order', 'product').filter(
                    alliance_partner_order__order_id=alliance_order_id,
                    alliance_partner_order__distributor__regionaldistributor__code=distributor_code
                ).create(product=Product.objects.filter(basepack_code=basepack_code).first(), quantity=0,
                         unitprice=0, price=0,
                         alliance_partner_order=AlliancePartnerOrder.objects.filter(
                    distributor__regionaldistributor__code=distributor_code,
                    order_id=alliance_order_id).first())

            # if order_inst.alliance_partner_order.order_status in (OrderStatus.INTRANSIT, OrderStatus.RECEIVED):
            #     subject = 'New invoice for a order no {}'.format(
            #         order_inst.alliance_partner_order_id)
            #     invoice_number = order_inst.alliance_partner_order.invoice_number_alliance
            #     distributor_name = order_inst.alliance_partner_order.distributor_name
            #     html_content = "Multiple invoices is received for order no {}, invoice_no {} and distributor_name {}".format(
            #         order_inst.alliance_partner_order_id, invoice_number, distributor_name)

            #     send_mail(subject, html_content,
            #               'no-reply@ishaktiapp.com',
            #               ['Shrishchandra.shukla@simtechitsolutions.in',
            #                   'farooque.patel@unilever.com', 'raghavendran.m@simtechitsolutions.in'],
            #               fail_silently=True)

            if order_inst.alliance_partner_order_id not in order_ids:
                order_ids.append(order_inst.alliance_partner_order_id)

            alliance_partner_order_id = order_inst.alliance_partner_order_id
            cld = order_inst.product.cld_configurations
            dispatch_quantity = int(float(row[12]))
            uom = row[13].upper()

            if uom in [self.UOM['CS'], self.UOM['CV'], self.UOM['DR']]:
                dispatch_quantity = (
                    order_inst.dispatch_quantity or 0) + dispatch_quantity * cld

            unitprice = float(row[16])

            if unitprice != order_inst.unitprice:
                order_inst.unitprice = unitprice

            order_inst.prd_discount = float(row[18] or 0)
            order_inst.add_discount = float(row[19] or 0)
            order_inst.sch_discount = float(row[20] or 0)
            order_inst.asch_discount = float(row[21] or 0)
            order_inst.disp_discount = float(row[22] or 0)
            order_inst.trade_discount = float(row[23] or 0)
            order_inst.cash_discount = float(row[24] or 0)
            discount_amount = order_inst.prd_discount + order_inst.add_discount + order_inst.sch_discount + \
                order_inst.asch_discount + order_inst.disp_discount + \
                order_inst.trade_discount + order_inst.cash_discount

            order_inst.batch_code = row[11]
            ########################################
            #year = int(row[45][0:4])
            #month  = int(row[45][4:6])
            #day = int(row[45][6:8])
            #prod_date =datetime(year, month, day)
            #order_inst.prod_date =prod_date or dt.now()
            #order_inst.base_price_par_unit =row[46]
            #order_inst.total_amt_base_peice =row[47]
            #############
            order_inst.dispatch_quantity = dispatch_quantity
            order_inst.dispatch_quantity = dispatch_quantity
            year = int(row[1][0:4])
            month = int(row[1][4:6])
            day = int(row[1][6:8])
            date_on = datetime(year, month, day)
            order_inst.dispatched_on = date_on or dt.now()
            net_amount = float(row[25])
            order_inst.discount_amount = discount_amount
            # if len(basepack_obj) == 0:
            #     order_inst.price = taxable_amount
            # import pdb; pdb.set_trace()
            if distributor_code in basepack_obj:
                if basepack_code in basepack_obj[distributor_code]:
                    order_inst.cgst = float(row[34])
                    cgst = order_inst.cgst_amount = float(
                        row[38]) + order_inst.cgst_amount or 0

                    order_inst.sgst = float(row[35])
                    sgst = order_inst.sgst_amount = float(
                        row[39]) + order_inst.sgst_amount or 0

                    order_inst.igst = float(row[33])
                    igst = order_inst.igst_amount = float(
                        row[37]) + order_inst.igst_amount or 0

                    order_inst.cess = float(row[36])
                    cess_amount = order_inst.cess_amount = float(
                        row[40]) + order_inst.cess_amount or 0
                    taxable_amount = net_amount - discount_amount

                    total_amount = taxable_amount + (
                        float(row[38]) + float(row[39]) + float(row[37]) + float(row[40]))
                    order_inst.price = net_amount + order_inst.price or 0
                else:
                    order_inst.cgst = float(row[34])
                    cgst = order_inst.cgst_amount = float(row[38])

                    order_inst.sgst = float(row[35])
                    sgst = order_inst.sgst_amount = float(row[39])

                    order_inst.igst = float(row[33])
                    igst = order_inst.igst_amount = float(row[37])

                    order_inst.cess = float(row[36])
                    cess_amount = order_inst.cess_amount = float(row[40])

                    taxable_amount = net_amount - discount_amount
                    order_inst.price = net_amount
                    total_amount = taxable_amount + \
                        (cgst + sgst + igst + cess_amount)
                basepack_obj[distributor_code].append(basepack_code)
            else:
                basepack_obj[distributor_code] = [basepack_code]
                order_inst.cgst = float(row[34])
                cgst = order_inst.cgst_amount = float(row[38])

                order_inst.sgst = float(row[35])
                sgst = order_inst.sgst_amount = float(row[39])

                order_inst.igst = float(row[33])
                igst = order_inst.igst_amount = float(row[37])

                order_inst.cess = float(row[36])
                cess_amount = order_inst.cess_amount = float(row[40])

                taxable_amount = net_amount - discount_amount
                order_inst.price = net_amount
                total_amount = taxable_amount + \
                    (cgst + sgst + igst + cess_amount)

            order_inst.item_status = OrderStatus.INTRANSIT
            order_inst.invoice_number_alliance = invoice_number_alliance
            order_inst.save()

            if alliance_partner_order_id not in alliance_partner_order:
                alliance_partner_order[alliance_partner_order_id] = {}
                alliance_partner_order[alliance_partner_order_id]['total_amount'] = 0
                alliance_partner_order[alliance_partner_order_id]['order_amount'] = 0
                alliance_partner_order[alliance_partner_order_id]['tax'] = 0
                alliance_partner_order[alliance_partner_order_id]['discount_amount'] = 0
                alliance_partner_order[alliance_partner_order_id]['cgst_total'] = 0
                alliance_partner_order[alliance_partner_order_id]['sgst_total'] = 0
                alliance_partner_order[alliance_partner_order_id]['order_id'] = alliance_partner_order_id
                alliance_partner_order[alliance_partner_order_id]['invoice_number_alliance'] = invoice_number_alliance

            if alliance_partner_order_id in alliance_partner_order and order_inst.item_status == OrderStatus.INTRANSIT:
                alliance_partner_order[alliance_partner_order_id]['order_amount'] += taxable_amount
                alliance_partner_order[alliance_partner_order_id]['tax'] += cgst + sgst + igst
                alliance_partner_order[alliance_partner_order_id]['total_amount'] += total_amount
                alliance_partner_order[alliance_partner_order_id]['discount_amount'] += discount_amount
                alliance_partner_order[alliance_partner_order_id]['cgst_total'] += cgst
                alliance_partner_order[alliance_partner_order_id]['sgst_total'] += sgst

                alliance_partner_order[alliance_partner_order_id]['invoice_number_alliance'] = invoice_number_alliance

                # print(alliance_partner_order[alliance_partner_order_id]['total_amount'])
        # import pdb; pdb.set_trace()
        AlliancePartnerOrderDetail.objects.filter(alliance_partner_order_id__in=order_ids,
                                                  item_status=OrderStatus.ORDERED).update(
            item_status=OrderStatus.CANCELLED)

        for order in alliance_partner_order.values():
            self._calaculate_order_amount(
                order['order_id'], order_inst.dispatched_on)
           # AlliancePartnerOrder.objects.filter( pk=order['order_id'] ).update(
            #    order_status=OrderStatus.INTRANSIT, dispatched_on=order_inst.dispatched_on,
            #   total_amount=round( order['total_amount'], 2 ), amount=order['order_amount'],
            #  tax=order['tax'], discount_amount=order['discount_amount'],
            # invoice_number_alliance=order['invoice_number_alliance'],cgst_total=order['cgst_total'],sgst_total=order['sgst_total'] )

    def _calaculate_order_amount(self, alliance_order_id, dispatched_on):
        order_detail_objs = AlliancePartnerOrderDetail.objects.filter(
            alliance_partner_order_id=alliance_order_id).filter(~Q(item_status=OrderStatus.CANCELLED), ~Q(item_status=OrderStatus.DISCARDED), ~Q(item_status=OrderStatus.RETURNED))

        order = AlliancePartnerOrder.objects.filter(id=alliance_order_id)

        gross_amount = order_detail_objs.aggregate(
            total=Sum(F('price') + F('discount_amount')))['total']
        total_amount = order_detail_objs.aggregate(total=Sum(
            F('price') + F('cgst_amount') + F('sgst_amount') + F('igst_amount') + F('cess_amount')))[
            'total']
        discount_amount = order_detail_objs.aggregate(
            total=Sum('discount_amount'))['total']

        invoice = order_detail_objs.values_list(
            "invoice_number_alliance", flat=True)
        invoice = [i for i in invoice if i]
        order.update(total_amount=total_amount, amount=gross_amount, discount_amount=discount_amount, invoice_number_alliance=",".join(
            set(invoice))[:-1], order_status=OrderStatus.INTRANSIT, dispatched_on=dispatched_on)

    def _remove_file(self, filename):
        try:
            os.remove(filename)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

    def calculate_received_total(self, po_id):
        # order_ids = AlliancePartnerOrder.objects.filter(created__gte='2019-10-01', created__lte='2019-11-30', order_status=OrderStatus.RECEIVED).values_list('id')
        order = AlliancePartnerOrder.objects.filter(id=po_id)

        order_detail_objs = AlliancePartnerOrderDetail.objects.filter(Q(alliance_partner_order_id=order),
                                                                      Q(item_status=OrderStatus.RECEIVED) | Q(
            item_status=OrderStatus.INTRANSIT))
        gross_amount = order_detail_objs.aggregate(
            total=Sum(F('price') + F('discount_amount')))['total']
        total_amount = order_detail_objs.aggregate(total=Sum(
            F('price') + F('cgst_amount') + F('sgst_amount') + F('igst_amount') + F('cess_amount')))[
            'total']
        discount_amount = order_detail_objs.aggregate(
            total=Sum('discount_amount'))['total']

        order.update(total_amount=total_amount, amount=gross_amount,
                     discount_amount=discount_amount)

        return order


class StockCorrection(object):
    '''
    stock correction command for RS
    '''

    # def get_ids(self, *args):
    #     # TODO: get list of user ids from their usernames
    #     pass

    def update_closing_stock(self):
        # to get the list of complete users importing and storing users in ids variable
        from app.models import RegionalDistributor
        ids = [obj.user_id for obj in RegionalDistributor.objects.all()]

        # distributor_ids = [3238, 3249]
        distributor_ids = [3167]

        data = tablib.Dataset()
        data.headers = ['Distributor Id', 'Distributor Name', 'Product Name', 'Product Id', 'Primary stock',
                        'Primary Amount', 'Secondary stock', 'Secondary Amount', 'Correct Updated Stock',
                        'Portal Stock', 'Portal Amount', 'Correct Updated Amount']
        for distributor_id in distributor_ids:
            distributor_name = User.objects.filter(
                id=distributor_id).values_list('name', flat=True)
            primary_order_details = self.get_alliance_partner_orders(
                distributor_id)
            secondary_order_details = self.get_distributor_orders(
                distributor_id)

            po_product_ids = list(
                map(lambda x: x['product'], primary_order_details))
            so_product_ids = list(
                map(lambda x: x['product'], secondary_order_details))
            unique_product_ids = set(po_product_ids + so_product_ids)
            for prod_id in unique_product_ids:
                product_obj = Product.objects.filter(
                    id=prod_id).values('basepack_name', 'tur')
                po = list(
                    filter(lambda x: x['product'] == prod_id, primary_order_details))
                so = list(
                    filter(lambda x: x['product'] == prod_id, secondary_order_details))

                if len(po) > 0:
                    if len(so) > 0:
                        updated_dispatch_units = po[0]['total_po_dispatch_quantity'] - so[0][
                            'total_so_dispatch_quantity']
                        if updated_dispatch_units == 0:
                            updated_amount = 0
                        else:
                            # updated_amount =  po[0]['total_po_amount'] - so[0]['total_so_amount']
                            updated_amount = updated_dispatch_units * \
                                product_obj[0]['tur']
                    else:
                        updated_dispatch_units = po[0]['total_po_dispatch_quantity']
                        updated_amount = updated_dispatch_units * \
                            product_obj[0]['tur']
                    actual_stock = DistributorStock.objects.filter(distributor_id=distributor_id,
                                                                   product_id=po[0]['product'],
                                                                   created__date=dt.now().date()).values_list(
                        'closing_stock', flat=True)
                    actual_amount = DistributorStock.objects.filter(distributor_id=distributor_id,
                                                                    product_id=po[0]['product'],
                                                                    created__date=dt.now().date()).values_list(
                        'amount', flat=True)

                    data.append([distributor_id, distributor_name[0] if len(distributor_name) > 0 else '',
                                 product_obj[0]['basepack_name'] if len(
                                     product_obj) > 0 else '', prod_id,
                                 po[0]['total_po_dispatch_quantity'], po[0]['total_po_amount'],
                                 so[0]['total_so_dispatch_quantity'] if len(
                                     so) > 0 else 0,
                                 so[0]['total_so_amount'] if len(
                                     so) > 0 else 0, updated_dispatch_units,
                                 actual_stock[0] if len(
                                     actual_stock) > 0 else '',
                                 actual_amount[0] if len(actual_amount) > 0 else '', updated_amount])

                # Comment it when you want to only generate the file and uncomment when you want to update the stock
                #     if updated_amount < 0:
                #         DistributorStock.objects.filter(distributor_id = distributor_id, product_id = po[0]['product'], created__date=dt.now().date()).update(
                #                 closing_stock=updated_dispatch_units)
                #     else:
                #         DistributorStock.objects.filter(distributor_id = distributor_id, product_id = po[0]['product'], created__date=dt.now().date()).update(
                #                 closing_stock=updated_dispatch_units, amount=updated_amount)
                else:
                    pass
        file_name = "DistributorStockData{0}.xls".format(
            dt.now().strftime('-%Y-%m-%d-%H-%M-%S'))
        with open(file_name, 'wb') as f:
            f.write(data.export('xls'))

    def get_alliance_partner_orders(self, distributor_id):

        po_obj = AlliancePartnerOrderDetail.objects.filter(alliance_partner_order__distributor_id=distributor_id,
                                                           alliance_partner_order__order_status=OrderStatus.RECEIVED,
                                                           item_status=OrderStatus.RECEIVED).values(
            'product').annotate(
            total_po_dispatch_quantity=Sum('dispatch_quantity'),
            total_po_amount=Sum('price') + Sum('cgst_amount') +
            Sum('sgst_amount') + Sum('igst_amount')
        ).values('product', 'total_po_dispatch_quantity', 'total_po_amount')

        return po_obj

    def get_distributor_orders(self, distributor_id):
        so_obj = DistributorOrderDetail.objects.filter(distributor_order__distributor_id=distributor_id,
                                                       distributor_order__order_status=OrderStatus.DISPATCHED,
                                                       item_status=OrderStatus.DISPATCHED).values(
            'product').annotate(
            total_so_dispatch_quantity=Sum('dispatch_quantity'), total_so_amount=Sum('net_amount')
        ).values('product', 'total_so_dispatch_quantity', 'total_so_amount')
        return so_obj


class FTPOrderFile(object):
    '''
    ftp generated file to remote location
    '''

    def __init__(self):
        self.host = settings.PIDILITE['FTP']['HOST']
        self.port = settings.PIDILITE['FTP']['PORT']
        self.username = settings.PIDILITE['FTP']['USER']
        self.password = settings.PIDILITE['FTP']['PASSWORD']
        self.inbound = settings.PIDILITE['FTP']['INBOUND']
        self.outbound = settings.PIDILITE['FTP']['OUTBOUND']
        self.archive = settings.PIDILITE['FTP']['ARCHIVE']
        self.matrd = settings.PIDILITE['FTP']['MATRD']
        self.gstno = settings.PIDILITE['FTP']['GSTNO']

    def connect(self):
        '''
        create connection to ftp
        '''
        from ftplib import FTP
        if not hasattr(self, 'con'):
            self.con = FTP(self.host, self.username, self.password)
        return self.con

    def upload_file(self, filepath, filename):
        '''
        upload generated file to ftp
        '''
        session = self.connect()
        session.cwd(self.inbound)
        file = open(filepath, 'rb')
        session.storbinary('STOR ' + filename, file)
        file.close()
        session.quit()

    def get_files(self):
        session = self.connect()

        if session.pwd() != join('/', self.outbound):
            session.cwd(self.outbound)
        filenames = session.nlst()

        for filename in filenames:
            self._download_file(filename)
            self._move_to_archive(filename)

        return filenames

    def _download_file(self, filename):
        session = self.connect()

        if session.pwd() != join('/', self.outbound):
            session.cwd(self.outbound)

        local_filename = join(settings.TMP_ROOT, filename)
        if 'matr_d' in local_filename.lower():
            try:
                with open(local_filename, 'wb') as f:
                    session.retrbinary('RETR %s' % filename, f.write)
            except IOError as e:
                logger.error(e)
                pass
        else:
            with open(local_filename, 'wb') as f:
                session.retrbinary('RETR %s' % filename, f.write)

    def _move_to_archive(self, filename):
        session = self.connect()
        file_source = join('/', self.outbound, filename)
        file_dest = join('/', self.archive, filename)
        session.rename(file_source.replace('\\', '/'),
                       file_dest.replace('\\', '/'))


class CancelOldOrders(object):

    def cancel_orders(self):
        order_detail = AlliancePartnerOrderDetail.objects.select_related('alliance_partner_order').filter(
            alliance_partner_order__created__date__lt=datetime.now(
            ).date() - timedelta(days=settings.CANCEL_BEFORE),
            alliance_partner_order__order_status=OrderStatus.ORDERED)

        if order_detail.exists():
            order_detail.update(
                item_status=OrderStatus.CANCELLED
            )
            AlliancePartnerOrder.objects.filter(
                id__in=order_detail.values_list('alliance_partner_order_id', flat=True)).update(
                order_status=OrderStatus.CANCELLED
            )

    def return_so_orders(self, distributor_id, order_ids, date):
        query = Q(distributor_id=distributor_id,
                  order_status=OrderStatus.DISPATCHED)
        if date:
            start_day = date+' 00:00:00'
            end_day = date+' 23:59:59'
            query = query & Q(dispatched_on__range=(start_day, end_day))
        elif order_ids != 'None' and len(order_ids.split(',')) > 0:
            query = query & Q(id__in=order_ids.split(','))
        so_orders = DistributorOrder.objects.filter(query)
        for order in so_orders:
            order.order_status = OrderStatus.RETURNED
            for dod in order.distributor_order_details.all():
                dod.item_status = OrderStatus.RETURNED
                dod.save()
            order.save()


class SFTPConnection(object):

    ssh = None
    sftp = None

    def connect(self, host, username, password=None, pkey=None, passpharse=None, port=22,):
        key = None
        if pkey:
            key = paramiko.RSAKey.from_private_key_file(
                pkey, password=passpharse)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, password=password,
                         pkey=key)
        self.sftp = self.ssh.open_sftp()

    def upload(self, source, target):
        self.sftp.put(source, target)

    def download(self, source, target):
        self.sftp.get(
            source, target)

    def list(self):
        print(self.sftp.listdir())

    def archive_file(self, path):
        pass

    def close(self):
        self.ssh.close()


class ProcessPepsicoInvoice():

    def _read_sftp_file(self):
        sftp = SFTPConnection()
        print("Reading Pepsioc invoice File from FTP")
        filename = "primary_invoice_pepsico.csv"
        target = os.path.join(settings.PEPSICO['TMP'], filename)
        sftp.connect(settings.PEPSICO['HOST'], settings.PEPSICO['USER'],
                     pkey=settings.PEPSICO['PKEY_PATH'], passpharse=settings.PEPSICO['PKEY_PASSWORD'])
        sftp.download(settings.PEPSICO['OUTBOUND'] +
                      filename, target)
        sftp.close()
        print("Download Inoice File completed")
        print(target)

        return target

    def process_pepsico_files(self):
        print("Processing Pespsico Invoice file")
        filename = r'D:\Work\projects\alliance-portal\doc\tmp\pepsico\primary_invoice_pepsico.csv'
        dataset = tablib.Dataset()
        dataset.csv = open(filename, 'rb').read()
        orders = {}
        valid_orders = []
        invalid_orders = []
        alliance_order_ids = []
        basepack_code_list = Product.objects.filter(
            partner_code=1003).values_list("basepack_code", flat=True)

        for row in dataset:
            order_details = {}
            order_details["invoice_number_alliance"] = row[0]
            order_details["bill_date"] = row[1]
            order_details["customer_code"] = row[2]
            order_details["po_date"] = row[5]
            order_details["mat_code"] = str(row[6])
            order_details["mat_name"] = row[7]
            order_details["batch_no"] = row[8]
            order_details["quantity"] = row[9]
            order_details["sales_uom"] = row[10]
            order_details["Inv_Qty_BaseUoM"] = int(row[11])
            order_details["base_uom"] = row[12]
            order_details["item_rate"] = float(row[13])
            order_details["add_discount"] = row[15]
            order_details["sch_discount"] = row[16]
            order_details["net_value"] = row[17]
            order_details["roundoff"] = row[18]
            order_details["igst_per"] = row[21]
            order_details["cgst_per"] = row[22]
            order_details["sgst_per"] = row[23]
            order_details["cess_per"] = row[24]
            order_details["igst_amt"] = row[25]
            order_details["cgst_amt"] = row[26]
            order_details["sgst_amt"] = row[27]
            order_details["cess_amount"] = row[28]
            order_details["tcs_amt"] = row[31]
            order_details["prod_date"] = row[33]
            order_details["en_code"] = row[34]
            order_details["unit_base_price"] = row[35]
            order_details["total_amount"] = row[36]
            po_no = row[4].split('/')
            alliance_order_id = po_no[-1]
            order_details["alliance_order_id"] = int(po_no[-1])
            order_details["distributor_code"] = int(po_no[0])
            if order_details["mat_code"] in basepack_code_list:
                order_details["is_mat_code_exist"] = True
                valid_orders.append(alliance_order_id)
            else:
                order_details["is_mat_code_exist"] = False
                invalid_orders.append(alliance_order_id)

            try:
                orders[alliance_order_id].append(order_details)
            except KeyError:
                orders[alliance_order_id] = [order_details]

        for item in set(valid_orders):
            for order in orders[item]:
                order_inst = AlliancePartnerOrderDetail.objects.select_related(
                    'alliance_partner_order', 'product').filter(
                    alliance_partner_order__order_id=order["alliance_order_id"],
                    product__basepack_code=order["mat_code"],
                    alliance_partner_order__distributor__regionaldistributor__code=order["distributor_code"], item_status=OrderStatus.ORDERED).first()
                if not order_inst:
                    order_inst = AlliancePartnerOrderDetail.objects.select_related(
                        'alliance_partner_order', 'product').filter(
                        alliance_partner_order__order_id=order["alliance_order_id"],
                        alliance_partner_order__distributor__regionaldistributor__code=order[
                            "distributor_code"]
                    ).create(product=Product.objects.get(basepack_code=order["mat_code"]), quantity=0,
                             unitprice=0, price=0,
                             alliance_partner_order=AlliancePartnerOrder.objects.filter(
                        distributor__regionaldistributor__code=order["distributor_code"],
                        order_id=order["alliance_order_id"]).first())

                cld = order_inst.product.cld_configurations

                order_inst.item_status = OrderStatus.INTRANSIT
                order_inst.unitprice = order["item_rate"]
                order_inst.dispatch_quantity = int(
                    float(order["Inv_Qty_BaseUoM"]))
                order_inst.invoice_number_alliance = order["invoice_number_alliance"]
                order_inst.add_discount = float(
                    order["add_discount"] or 0)
                order_inst.sch_discount = float(
                    order["sch_discount"] or 0)
                order_inst.batch_code = order["batch_no"]
                year = int(order_details["prod_date"][0:4])
                month = int(order_details["prod_date"][4:6])
                day = int(order_details["prod_date"][6:8])
                prod_date = datetime(year, month, day)
                order_inst.prod_date = prod_date or dt.now()
                order_inst.base_price_par_unit = order["unit_base_price"]
                order_inst.total_amt_base_peice = order["total_amount"]
                order_inst.cgst = float(order["cgst_per"])
                cgst = order_inst.cgst_amount = float(
                    order["cgst_amt"])
                order_inst.sgst = float(order["sgst_per"])
                sgst = order_inst.sgst_amount = float(
                    order["sgst_amt"])
                order_inst.igst = float(order["igst_per"])
                igst = order_inst.igst_amount = float(
                    order["igst_amt"])
                order_inst.cess = float(order["cess_per"])
                cess_amount = order_inst.cess_amount = float(
                    order["cess_amount"])
                year = int(order["bill_date"][0:4])
                month = int(order["bill_date"][4:6])
                day = int(order["bill_date"][6:8])
                date_on = datetime(year, month, day)
                order_inst.dispatched_on = date_on or dt.now()
                net_amount = float(order["net_value"])
                order_inst.price = float(order["net_value"])
                order_inst.discount_amount = order_inst.add_discount + order_inst.sch_discount
                order_inst.save()

                if order_inst.alliance_partner_order_id not in alliance_order_ids:
                    alliance_order_ids.append(
                        order_inst.alliance_partner_order_id)

        for id in alliance_order_ids:
            self._calaculate_order_amount(id)
        print("Pepsico Invoice read completed")

    def _calaculate_order_amount(self, alliance_order_id):
        order_detail_objs = AlliancePartnerOrderDetail.objects.filter(
            alliance_partner_order_id=alliance_order_id).filter(~Q(item_status=OrderStatus.CANCELLED), ~Q(item_status=OrderStatus.DISCARDED), ~Q(item_status=OrderStatus.RETURNED))

        order = AlliancePartnerOrder.objects.filter(id=alliance_order_id)

        gross_amount = order_detail_objs.aggregate(
            total=Sum(F('price') + F('discount_amount')))['total']
        total_amount = order_detail_objs.aggregate(total=Sum(
            F('price') + F('cgst_amount') + F('sgst_amount') + F('igst_amount') + F('cess_amount')))[
            'total']
        discount_amount = order_detail_objs.aggregate(
            total=Sum('discount_amount'))['total']

        invoice = order_detail_objs.values_list(
            "invoice_number_alliance", flat=True)
        invoice = [i for i in invoice if i]
        order.update(total_amount=total_amount, amount=gross_amount, discount_amount=discount_amount, invoice_number_alliance=",".join(
            set(invoice))[:-1], order_status=OrderStatus.INTRANSIT, dispatched_on=dt.now())
