import time,os
import csv
from .sql import OrderAdvanceFilter
from hul.choices import OrderStatus
from django.conf import settings
from django.utils.timezone import localtime
from hul.celery import app as celery_app
from celery_progress.backend import ProgressRecorder
from django.utils import timezone as dt
from django.http.request import QueryDict
from ntpath import join


@celery_app.task(name="misreporting.tasks.export_to_excel")
def export_to_excel(params, order_type):
    progress_recorder = ProgressRecorder(export_to_excel)
    data = QueryDict(params)
    order_data = OrderAdvanceFilter.get_filtered_data(data)
    count = len(list(order_data))

    if order_type == OrderAdvanceFilter.ALIANCE_ORDER_QUERY:
        filename = 'primary_orders_' + dt.datetime.today().strftime("%d%m%Y%H%M%S") + ".csv"
    elif order_type == OrderAdvanceFilter.DISTRIBUTOR_ORDER_QUERY:
        filename = 'secondary_orders_' + \
            dt.datetime.today().strftime("%d%m%Y%H%M%S") + ".csv"
    filepath = os.path.join(settings.EXPORT_PATH, "temp", filename)
    writer = csv.writer(open(filepath, 'wb'))
    if order_type == OrderAdvanceFilter.ALIANCE_ORDER_QUERY:
        writer.writerow([
            'Invoice Number',
            'Invoice Date',
            'Ordered Date',
            'Invoice Value',
            'Place of Supply',
            'Brand',
            'Distributor',
            'PIL CODE',
            'HUL CODE',
            'GST Number',
            'MoC',
            'Basepack Name',
            'Basepack code',
            'Cases',
            'Units',
            'Base Price',
            'CGST Amount',
            'SGST Amount',
            'IGST Amount',
            'Total Amount',
            'Item Status',
            'Payment Status',
            'HSN Code'
        ])

        for i, row in enumerate(order_data):
            progress_recorder.set_progress(i + 1, count)
            item_status = OrderStatus.LABEL[row.item_status]
            order_date = localtime(row.created).strftime(
                settings.DATETIME_FORMAT_CSV)
            dispatched_date = localtime(row.dispatched_on).strftime(
                settings.DATETIME_FORMAT_CSV) if row.dispatched_on else ''
            writer.writerow([
                row.invoice_number,
                dispatched_date,
                order_date,
                row.total_amount,
                row.place_of_supply,
                row.alliance_name,
                row.distributor_name,
                row.distributor.regionaldistributor.code,
                row.distributor.regionaldistributor.hul_code,
                row.gst_code,
                row.moc_name,
                row.basepack_name,
                row.basepack_code,
                row.cases,
                row.quantity,
                row.unitprice,
                row.cgst_amount,
                row.sgst_amount,
                row.igst_amount,
                row.net_amount,
                item_status,
                row.get_payment_status_display(),
                row.hsn_code
            ])

    elif order_type == OrderAdvanceFilter.DISTRIBUTOR_ORDER_QUERY:
        writer.writerow([
            'Invoice Number',
            'Invoice Date',
            'Ordered Date',
            'Invoice Value',
            'Place of Supply',
            'Brand',
            'Redistribution Stockist',
            'PIL CODE',
            'HUL CODE',
            'Rural Sales Promoter',
            'Shakti Entrepreneur Code',
            'Shakti Entrepreneur',
            'GST Number',
            'MoC',
            'Basepack Name',
            'Basepack code',
            'Cases',
            'Units',
            'Base Price',
            'CGST Amount',
            'SGST Amount',
            'IGST Amount',
            'Total Amount',
            'Item Status',
            'Payment Status',
            'HSN Code',
            'Taxable Value',
            'Units Per Cases',
            'CGST RATE',
            'SGST RATE',
            'IGST RATE'
        ])

        for i, row in enumerate(order_data):
            progress_recorder.set_progress(i + 1, count)
            item_status = OrderStatus.LABEL[row.item_status]
            order_date = localtime(row.created).strftime(
                settings.DATETIME_FORMAT_CSV)
            dispatched_date = localtime(row.dispatched_on).strftime(
                settings.DATETIME_FORMAT_CSV) if row.dispatched_on else ''
            writer.writerow([
                row.invoice_number,
                dispatched_date,
                order_date,
                row.total_amount,
                row.place_of_supply,
                row.alliance_name,
                row.distributor_name, row.distributor.regionaldistributor.code,
                row.distributor.regionaldistributor.hul_code,
                row.rsp_id,
                row.shakti_enterpreneur_code,
                row.shakti_enterpreneur_name,
                row.gst_code,
                row.moc_name,
                row.basepack_name,
                row.basepack_code,
                row.cases,
                row.quantity,
                row.unitprice,
                row.cgst_amount,
                row.sgst_amount,
                row.igst_amount,
                row.net_amount,
                item_status,
                row.get_payment_status_display(),
                row.hsn_code,
                row.price,
                row.cld_configurations,
                row.cgst,
                row.sgst,
                row.igst
            ])
    return filename
