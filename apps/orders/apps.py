'''Order App Config '''
from __future__ import unicode_literals

from django.apps import AppConfig


class OrdersConfig(AppConfig):
    '''
    Order Config
    '''
    name = 'orders'

    def ready(self):
        import orders.signals
