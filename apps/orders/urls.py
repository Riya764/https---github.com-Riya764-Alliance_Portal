'''order/urls.py'''
from django.conf.urls import url
from .views import (DistributerOrderInvoiceView, AllianceOrderInvoiceView,
                    dispatch_stockist_order, add_product_secondary_order)
from .api import Orders

urlpatterns = [
    url(r'^orders/$', Orders.as_view(), name='orderhistory'),
    url(r'^distributer-order-invoice/(?P<order_invoice>[0-9]+)$',
        DistributerOrderInvoiceView.as_view(),
        name='distributer-order-invoice', kwargs={'invoice': True}),
    url(r'^alliance-order-invoice/(?P<order_invoice>[0-9]+)$',
        AllianceOrderInvoiceView.as_view(), name='alliance-order-invoice',
        kwargs={'invoice': True}),
    # url(r'^admin/orders/dispatch/alliance/(?P<order_id>[0-9]+)$',
    #     dispatch_alliance_order, name='dispatch_alliance_order'),
    url(r'^admin/orders/dispatch/stockist/(?P<order_id>[0-9]+)$',
        dispatch_stockist_order, name='dispatch_stockist_order'),
    url(r'^admin/orders/secondary/product/add',
        add_product_secondary_order, name='add_product_secondary_order'),
]
