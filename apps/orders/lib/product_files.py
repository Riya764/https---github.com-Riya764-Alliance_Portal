
import tablib
import os
import errno
from datetime import datetime
from os.path import join
from django.utils import timezone as dt
from django.conf import settings
from orders.models import AlliancePartnerOrderDetail, AlliancePartnerOrder
from product.models import Product, ProductChild
from orders.lib.order_management import CalculatePrice
from order_files import FTPOrderFile
from hul.choices import OrderStatus
from django.core.mail import send_mail
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class ProductFile():
    #  if 'out_autoandpushwssporesult' in filename.lower():
    #                 # status file update
    #                 self._update_status_data(filepath)
    #             elif 'rb_autopo_invoice' in filename.lower():
    #                 # quantity/discount update
    #                 self._process_data(filepath)
    def process_product_files(self):
        ftp_obj = FTPProductFile()
        filenames = ftp_obj.get_files()
        for filename in filenames:
            filepath = join(settings.TMP_ROOT, filename)
            try:
                if 'matrd' in filename.lower():
                    self._process_data(filepath)
                elif 'hsn code' in filename.lower():
                    self.process_hsn_data(filepath)
            except Exception as e:
                logger.error(e)
                pass

            self._remove_file(filepath)

    def process_hsn_data(self, filename):
        dataset = tablib.Dataset()
        dataset.xlsx = open(filename, 'rb').read()

        for row in dataset:
            data = {
                "hsn_code": row[3],
                "basepack_code": row[1]
            }
            product_hsn_obj = Product.objects.filter(
                basepack_code = data.get('basepack_code')
                ).update(hsn_code = data.get('hsn_code')
            )

    def _process_data(self, filename):
        dataset = tablib.Dataset()
        dataset.csv = open(filename, 'rb').read()

        for row in dataset:
            try:
                product_basepack_code = Product.objects.get(basepack_code=row[1].strip())
            except Exception as e:
                logger.error(e)
                subject = 'Error while processing product code file,'\
                          ' product code no. {} does not exist'.format(row[1].strip())
                html_content = str(e)
                send_mail(subject, html_content,
                          'no-reply@ishaktiapp.com',
                          ['farooque.patel@unilever.com', 'sunil.kumar.14@netsolutions.com', 'prasenjit.jha@netsolutions.com'],
                          fail_silently=True)
            data={
                "child_basepack_code": row[0].strip(),
                "mother_basepack_code": product_basepack_code
            }
            if data.get('mother_basepack_code'):
                product_obj = ProductChild.objects.update_or_create(
                    child_basepack_code = data.get('child_basepack_code'),
                    mother_basepack_code = data.get('mother_basepack_code'),
                    defaults=data
                )

    def _remove_file(self, filename):
        try:
            os.remove(filename)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

class FTPProductFile(FTPOrderFile):

    def get_files(self):
        session = self.connect()

        if session.pwd() != join('/', self.matrd):
            session.cwd(self.matrd)
        filenames = session.nlst()

        for filename in filenames:
            self._download_file(filename)
            self._move_to_archive(filename)

        return filenames

    def _download_file(self, filename):
        session = self.connect()

        if session.pwd() != join('/', self.matrd):
            session.cwd(self.matrd)

        local_filename = join(settings.TMP_ROOT, filename)

        with open(local_filename, 'wb') as f:
            session.retrbinary('RETR %s' % filename, f.write)

    def _move_to_archive(self, filename):
        session = self.connect()
        file_source = join('/', self.matrd, filename)
        file_time = datetime.now().strftime("_%Y-%m-%d_%I-%M-%S_%p.")
        split_filename = filename.split('.')
        file_dest = join('/', self.archive, split_filename[0]+file_time+split_filename[1])
        session.rename(file_source.replace('\\', '/'),file_dest.replace('\\', '/'))