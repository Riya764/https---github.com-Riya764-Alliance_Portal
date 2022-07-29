'''
misreporting proxy models
'''
from __future__ import unicode_literals
import csv
from django.db import models
from django.http import HttpResponse
from django.utils import timezone as dt
from .sql import RsLevelFilter, RspLevelFilter
from orders.models import DistributorOrder


class AdvanceSearch(DistributorOrder):
    ''' advance search model for diplaying advance filter '''
    class Meta:
        proxy = True
        verbose_name_plural = 'Data'
        verbose_name = 'Data'


class SeLevel(DistributorOrder):
    ''' shakit wise report '''
    class Meta:
        proxy = True
        verbose_name_plural = 'Shakti Entrepreneur Level'
        verbose_name = 'Shakti Entrepreneur Level'


class BasePackLevel(DistributorOrder):
    ''' shakit wise report '''
    class Meta:
        proxy = True
        verbose_name_plural = 'Base Pack Level'
        verbose_name = 'Base Pack Level'


class BasepkLevelFormat(DistributorOrder):
    ''' shakit wise report '''
    class Meta:
        proxy = True
        verbose_name_plural = 'Base Pack Level Format'
        verbose_name = 'Base Pack Level Format'


class BillCount(DistributorOrder):
    ''' shakit wise report '''
    class Meta:
        proxy = True
        verbose_name_plural = 'Bill Count Data'
        verbose_name = 'Bill Count Data'


class RsLevel(DistributorOrder):
    ''' RS wise report '''
    class Meta:
        proxy = True
        verbose_name_plural = 'RS Level'
        verbose_name = 'RS Level'

    @staticmethod
    def get_csv_data(request):
        order_data, eco_data, eco_count = RsLevelFilter.get_filtered_data(request.GET)
        filename = dt.datetime.today().strftime("%d%m%Y")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="RS Level Report %s.csv"' % filename

        writer = csv.writer(response)
        writer.writerow([
            'SALES',
            '',
            '',
            '',
            ''
        ])
        writer.writerow([
            'RS Name',
            'MOC',
            'ORDERED TOTAL COST',
            'DISPATCHED TOTAL COUNT',
            'GRAND TOTAL',

        ])

        for record in order_data:
            rs_name = ''
            if record['distributor__name'] != None:
                rs_name = record['distributor__name']

            writer.writerow([
                rs_name,
                record['moc_name'],
                record['ordered'],
                record['dispatched'],
                record['grandtotal']
            ])

        ordered_total_cost = dispatched_total_cost = total_grandtotal = 0
        ordered_shkti = dispatched_shkti = total_shkti = 0
        if order_data:
            ordered_total_cost = sum(
                map(lambda x: x['ordered'] or 0, order_data))
            dispatched_total_cost = sum(
                map(lambda x: x['dispatched'] or 0, order_data))
            total_grandtotal = sum(
                map(lambda x: x['grandtotal'] or 0, order_data))
        if eco_data:
            ordered_shkti = sum(map(lambda x: x['ordered'] or 0, eco_data))
            dispatched_shkti = sum(
                map(lambda x: x['dispatched'] or 0, eco_data))
            total_shkti = len(eco_data)

        writer.writerow([
            'Grand Total',
            '',
            ordered_total_cost,
            dispatched_total_cost,
            total_grandtotal
        ])

        writer.writerow([
            '',
            '',
            '',
            ''
        ])
        writer.writerow([
            '',
            '',
            '',
            ''
        ])
        writer.writerow([
            'ECO',
            '',
            '',
            ''
        ])
        writer.writerow([
            'SHAKTI ENTERPRENEUR',
            'RS Name',
            'MoC',
            'ORDERED',
            'DISPATCHED',

        ])

        for record in eco_data:
            rs_name = ''
            if record['distributor__name'] != None:
                rs_name = record['distributor__name']

            writer.writerow([
                record['shakti_enterpreneur__shakti_user__code'],
                rs_name,
                record['moc_name'],
                record['ordered'],
                record['dispatched'],
            ])
        writer.writerow([
            'Grand Total',
            '',
            '',
            ordered_shkti,
            dispatched_shkti,
        ])

        writer.writerow([
            'Unique Eco Total',
            '',
            '',
            '',
            eco_count,
        ])
        return response


class RspLevel(DistributorOrder):
    ''' RSP wise report '''
    class Meta:
        proxy = True
        verbose_name_plural = 'RSP Level'
        verbose_name = 'RSP Level'

    @staticmethod
    def get_csv_data(request):
        order_data, eco_data, eco_count = RspLevelFilter.get_filtered_data(request.GET)
        filename = dt.datetime.today().strftime("%d%m%Y")
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="RSP Level Report %s.csv"' % filename

        writer = csv.writer(response)
        writer.writerow([
            'SALES',
            '',
            '',
            ''
        ])
        writer.writerow([
            'RSP',
            'State',
            'MoC',
            'ORDERED TOTAL COST',
            'DISPATCHED TOTAL COUNT',
            'GRAND TOTAL',

        ])

        for record in order_data:
            rs_name = ''
            if record['sales_promoter__regionalsalespromoter__rsp_id'] != None:
                rs_name = record['sales_promoter__regionalsalespromoter__rsp_id']

            writer.writerow([
                rs_name,
                record['shipping_address__state__name'],
                record['moc_name'],
                record['ordered'],
                record['dispatched'],
                record['grandtotal']
            ])

        ordered_total_cost = dispatched_total_cost = total_grandtotal = 0
        ordered_shkti = dispatched_shkti = total_shkti = 0
        if order_data:
            ordered_total_cost = sum(
                map(lambda x: x['ordered'] or 0, order_data))
            dispatched_total_cost = sum(
                map(lambda x: x['dispatched'] or 0, order_data))
            total_grandtotal = sum(
                map(lambda x: x['grandtotal'] or 0, order_data))
        if eco_data:
            ordered_shkti = sum(map(lambda x: x['ordered'] or 0, eco_data))
            dispatched_shkti = sum(
                map(lambda x: x['dispatched'] or 0, eco_data))
            total_shkti = len(eco_data)

        writer.writerow([
            'Grand Total',
            '',
            '',
            ordered_total_cost,
            dispatched_total_cost,
            total_grandtotal
        ])

        writer.writerow([
            '',
            '',
            '',
            ''
        ])
        writer.writerow([
            '',
            '',
            '',
            ''
        ])
        writer.writerow([
            'ECO',
            '',
            '',
            ''
        ])
        writer.writerow([
            'SHAKTI ENTERPRENEUR',
            'RSP',
            'MoC',
            'ORDERED',
            'DISPATCHED',
        ])

        for record in eco_data:
            shakti = ''
            if record['shakti_enterpreneur__shakti_user__code'] != None:
                shakti = record['shakti_enterpreneur__shakti_user__code']
            rs_name = ''
            if record['sales_promoter__regionalsalespromoter__rsp_id'] != None:
                rs_name = record['sales_promoter__regionalsalespromoter__rsp_id']

            writer.writerow([
                shakti,
                rs_name,
                record['moc_name'],
                record['ordered'],
                record['dispatched'],
            ])
        writer.writerow([
            'Grand Total',
            '',
            '',
            ordered_shkti,
            dispatched_shkti,
        ])
        writer.writerow([
            'Unique Eco Total',
            '',
            '',
            '',
            eco_count,
        ])
        return response
