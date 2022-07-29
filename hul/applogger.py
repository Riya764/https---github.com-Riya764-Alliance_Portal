from datetime import datetime, timedelta, time
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
import logging
from django.utils import timezone

class AppLogger(object):

    # @staticmethod
    # def debug_log(comment, source='', tag=''):
    #     try:
    #         logger = logging.getLogger('guardapp')
    #         formatted_log = '{} {} {} {}'.format(
    #             str(timezone.now()), source, comment, tag)
    #         logger.debug(formatted_log)
    #     except:
    #         pass

    @staticmethod
    def info_log(comment, source={}, tag=''):
        try:
            logger = logging.getLogger('hul')
            formatted_log = '{} {} {} {}'.format(
                str(timezone.now()), source, comment, tag)
            logger.info(formatted_log)
        except:
            pass

    @staticmethod
    def error_log(comment, source='', tag=''):
        try:
            logger = logging.getLogger('hul')
            formatted_log = '{} {} {} {}'.format(
                str(timezone.now()), source, comment, tag)
            logger.error(formatted_log)
        except:
            pass
