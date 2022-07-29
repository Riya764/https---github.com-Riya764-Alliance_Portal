import tablib
import os
import errno
from os.path import join
from django.utils import timezone as dt
from django.conf import settings
from app.models import RegionalDistributor
from order_files import FTPOrderFile
from hul.choices import OrderStatus
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

class GstFile():
    def process_gst_files(self):
        ftp_obj = FTPRsGstFile()
        filenames = ftp_obj.get_files()
        for filename in filenames:
            filepath = join(settings.TMP_ROOT, filename)
            try:
                self.process_gst_data(filepath)
            except Exception as e:
                logger.error(e)
                pass

            self._remove_file(filepath)

    def process_gst_data(self, filename):
        # import pdb; pdb.set_trace()
        dataset = tablib.Dataset()
        dataset.csv = open(filename, 'rb').read()
        
        for row in dataset:
            data = {
                "gst_code": row[4],
                "pil_code": row[2]
            }
            
            rs_gst_obj = RegionalDistributor.objects.filter(
                code = data.get('pil_code')
                ).update(gst_code = data.get('gst_code')
            )
    
    def _remove_file(self, filename):
        try:
            os.remove(filename)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise

class FTPRsGstFile(FTPOrderFile):

    def get_files(self):
        session = self.connect()
        if session.pwd() != join('/', self.gstno):
            session.cwd(self.gstno)
        filenames = session.nlst()

        for filename in filenames:
            self._download_file(filename)
            # self._move_to_archive(filename)

        return filenames

    def _download_file(self, filename):
        session = self.connect()

        if session.pwd() != join('/', self.gstno):
            session.cwd(self.gstno)

        local_filename = join(settings.TMP_ROOT, filename)

        with open(local_filename, 'wb') as f:
            session.retrbinary('RETR %s' % filename, f.write)

    def _move_to_archive(self, filename):
        session = self.connect()
        file_source = join('/', self.gstno, filename)
        file_dest = join('/', self.archive, filename)
        session.rename(file_source.replace('\\', '/'),file_dest.replace('\\', '/'))