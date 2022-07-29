'''sql queries'''
from django.db import connection
from django.db.models import (Case, CharField, Count, F, FloatField, Func,
                              IntegerField, Q, Sum, Value, When)
from django.db.models.functions import Coalesce, Concat

from hul.choices import OrderStatus
from hul.constants import ADMIN_PAGE_SIZE
from hul.utility import MOC
from orders.models import (AlliancePartnerOrder, DistributorOrder,
                           DistributorOrderDetail)


class RspLevelFilter(object):
    '''
    rsp level filter
    '''
    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        sales_queryset = RspLevelFilter._get_ordered_sql(request_filter_list)
        eco_queryset, eco_count = RspLevelFilter._get_eco_sql(request_filter_list)
        return sales_queryset, eco_queryset, eco_count

    # @staticmethod
    # def _get_ordered_sql(request_filter_list, status):
    #     queryset = DistributorOrder.objects.filter(order_status__in=[1,5])
    #     start_date = request_filter_list.get('start_date', None)
    #     end_date = request_filter_list.get('end_date', None)
    #     sales_promoter = request_filter_list.get('sales_promoter', None)

    #     if start_date:
    #         queryset = queryset.filter(created__gte=start_date)
    #     if end_date:
    #         queryset = queryset.filter(created__lte=end_date)
    #     if sales_promoter:
    #         queryset = queryset.filter(sales_promoter_id=sales_promoter)

    #     order_data =  queryset.order_by('created')

    #     mocdata = MOC.calculate_moc(start_date, end_date, order_data)

    #     return mocdata

    @staticmethod
    def _get_ordered_sql(request_filter_list):
        queryset = DistributorOrder.objects.filter(order_status__in=(1, 5), moc__isnull=False)
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        sales_promoter = request_filter_list.get('sales_promoter', None)
        states = request_filter_list.getlist('state', default=None)
        mocs = request_filter_list.getlist('moc', default=None)
        alliance_partner = request_filter_list.get('alliance_partner', None)

        if alliance_partner:
            queryset = queryset.filter(distributor__regionaldistributor__alliance_partner__user=alliance_partner)
            # queryset = queryset.filter(product__brand__user=alliance_partner)
        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if states:
            state_ids = tuple([x.encode("utf-8") for x in states])
            queryset = queryset.filter(shipping_address__state__in=state_ids)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(moc__in=moc_ids)

        if sales_promoter:
            queryset = queryset.filter(sales_promoter_id=sales_promoter)

        return queryset.annotate(sales=Count('sales_promoter_id')
                                 ).values('sales').annotate(
            ordered=Coalesce(Sum(
                Case(When(order_status=OrderStatus.ORDERED, then=F('total_amount')),
                     output_field=FloatField())
            ), 0),
            dispatched=Coalesce(Sum(
                Case(When(order_status=OrderStatus.DISPATCHED, then=F('total_amount')),
                     output_field=FloatField())
            ), 0),
            grandtotal=Coalesce(Sum(
                Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount')),
                     output_field=FloatField())
            ), 0),
            moc_name=Concat('moc__name', Value('-'), 'moc__moc_year__year', output_field=CharField())
        ).values(
            'sales', 'ordered', 'dispatched', 'grandtotal', 'moc_name', 'moc'
        ).annotate(
            moc_amount=Coalesce(Sum('total_amount'),0)
        ).values('moc_amount', 'moc', 'sales', 'ordered', 'dispatched', 'grandtotal', 'sales_promoter__regionalsalespromoter__rsp_id', 'shipping_address__state__name', 'moc_name').order_by(
            'sales_promoter__name', 'moc__moc_year__year', 'moc__start_date', 'moc_name'
        )

    # @staticmethod
    # def _get_eco_sql(request_filter_list):
    #     queryset = DistributorOrder.objects.filter(order_status__in=(1, 5))
    #     start_date = request_filter_list.get('start_date', None)
    #     end_date = request_filter_list.get('end_date', None)
    #     sales_promoter = request_filter_list.get('sales_promoter', None)
    #     states = request_filter_list.getlist('state', default=None)
    #     mocs = request_filter_list.getlist('moc', default=None)
    #     alliance_partner = request_filter_list.get('alliance_partner', None)

    #     if alliance_partner:
    #         queryset = queryset.filter(distributor__regionaldistributor__alliance_partner__user=alliance_partner)
    #         # queryset = queryset.filter(product__brand__user=alliance_partner)
    #     if start_date:
    #         queryset = queryset.filter(created__date__gte=start_date)
    #     if end_date:
    #         queryset = queryset.filter(created__date__lte=end_date)
    #     if states:
    #         state_ids = tuple([x.encode("utf-8") for x in states])
    #         queryset = queryset.filter(shipping_address__state__in=state_ids)
    #     if mocs:
    #         moc_ids = tuple([x.encode("utf-8") for x in mocs])
    #         queryset = queryset.filter(moc__in=moc_ids)
    #     if sales_promoter:
    #         queryset = queryset.filter(sales_promoter_id=sales_promoter)

    #     queryset = queryset.annotate(sales=Count('shakti_enterpreneur_id', distinct=True)
    #                              ).values('sales').annotate(
    #         ordered=Count(
    #             Case(When(order_status=OrderStatus.ORDERED, then=F('total_amount')),
    #                  output_field=FloatField())
    #         ),
    #         dispatched=Count(
    #             Case(When(order_status=OrderStatus.DISPATCHED, then=F('total_amount')),
    #                  output_field=FloatField())
    #         ),
    #         grandtotal=Count(
    #             Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount')),
    #                  output_field=FloatField())
    #         )
    #     ).values('sales', 'ordered', 'dispatched', 'grandtotal', 'sales_promoter__name')


    #     return queryset

    @staticmethod
    def _get_eco_sql(request_filter_list):
        queryset = DistributorOrder.objects.filter(order_status__in=(1, 5))
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        sales_promoter = request_filter_list.get('sales_promoter', None)
        states = request_filter_list.getlist('state', default=None)
        mocs = request_filter_list.getlist('moc', default=None)
        alliance_partner = request_filter_list.get('alliance_partner', None)

        if alliance_partner:
            queryset = queryset.filter(distributor__regionaldistributor__alliance_partner__user=alliance_partner)
            # queryset = queryset.filter(product__brand__user=alliance_partner)
        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if states:
            state_ids = tuple([x.encode("utf-8") for x in states])
            queryset = queryset.filter(shipping_address__state__in=state_ids)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(moc__in=moc_ids)
        if sales_promoter:
            queryset = queryset.filter(sales_promoter_id=sales_promoter)

        queryset = queryset.values(
            'shakti_enterpreneur_id'
        ).annotate(
            sales=Count('shakti_enterpreneur_id', distinct=True)
        )

        eco_count = queryset.aggregate(eco_count = Sum('sales'))['eco_count'] or 0
        queryset = queryset.values('shakti_enterpreneur_id', 'sales').annotate(
            ordered=Count(
                Case(When(order_status=OrderStatus.ORDERED, then=F('total_amount')),
                     output_field=FloatField())
            ),
            dispatched=Count(
                Case(When(order_status=OrderStatus.DISPATCHED, then=F('total_amount')),
                     output_field=FloatField())
            ),
            grandtotal=Count(
                Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount')),
                     output_field=FloatField())
            ),
            moc_name=Concat('moc__name', Value('-'), 'moc__moc_year__year', output_field=CharField())
        ).values('shakti_enterpreneur_id', 'sales', 'ordered', 'dispatched', 'grandtotal', 'sales_promoter__regionalsalespromoter__rsp_id', 'shakti_enterpreneur__shakti_user__code', 'moc_name').order_by(
            'sales_promoter__name', 'shakti_enterpreneur__name', 'moc__moc_year__year', 'moc__start_date', 'moc_name'
        )
        return queryset , eco_count


class OrderAdvanceFilter(object):
    ''' Advanced Filter '''

    _ALIANCE_FILTER_RAW_SQL = ''' SELECT apo.id as id, apo.invoice_number as invoice_number,
    apo.order_status as order_status, aua.name as alliance_name, aurd.name as distributor_name,
    apo.total_amount as total_amount,
    Concat(mmm.name,'-',mmy.year) as moc_name,
    apod.price as item_price, apo.created as created, lsa.name as place_of_supply, apo.dispatched_on as dispatched_on, apo.total_amount as total_amount,
    apo.payment_status as payment_status, apod.item_status, apod.dispatch_quantity as dispatch_quantity, apod.unitprice as unitprice, apod.cgst_amount as cgst_amount,
    apod.sgst_amount as sgst_amount, apod.igst_amount as igst_amount, pp.basepack_name as basepack_name, pp.basepack_code as basepack_code, pp.hsn_code as hsn_code, ard.gst_code as gst_code,
    -- mod(apod.quantity, pp.cld_configurations) as quantity, div(apod.quantity, pp.cld_configurations) as cases,
    apod.price - apod.discount_amount + apod.sgst_amount + apod.cgst_amount + apod.igst_amount as net_amount,
    CASE WHEN apod.dispatch_quantity > 0 THEN mod(apod.dispatch_quantity, pp.cld_configurations)
		ELSE mod(apod.quantity, pp.cld_configurations)
		END as quantity,
	CASE WHEN apod.dispatch_quantity > 0 THEN div(apod.dispatch_quantity, pp.cld_configurations)
		ELSE div(apod.quantity, pp.cld_configurations)
		END as cases
    FROM orders_alliancepartnerorder as apo
    LEFT JOIN orders_alliancepartnerorderdetail as apod ON (apod.alliance_partner_order_id = apo.id)
    LEFT JOIN product_product as pp ON (pp.id = apod.product_id)
    LEFT JOIN app_user as aurd ON (aurd.id = apo.distributor_id)
    LEFT JOIN app_user as aua ON (aua.id = apo.alliance_id)
    LEFT JOIN app_regionaldistributor as ard ON (ard.user_id = apo.distributor_id)
    LEFT JOIN app_useraddress as apua ON (apua.id = apo.shipping_address_id)
    LEFT JOIN localization_state as lsa ON (lsa.id = apua.state_id)
    LEFT JOIN moc_mocmonth as mmm ON (mmm.id = apo.moc_id)
	LEFT JOIN moc_mocyear as mmy ON (mmy.id = mmm.moc_year_id)'''

    _DISTRIBUTOR_FILTER_RAW_SQL = ''' SELECT dto.id as id, dto.invoice_number as invoice_number, lsa.name as place_of_supply, arsp.rsp_id as rsp_id,
    dto.order_status as order_status, aua.name as alliance_name, aurd.name as distributor_name, ard.gst_code as gst_code,
    ause.name as shakti_enterpreneur_name, dto.total_amount as total_amount,
    Concat(mmm.name,'-',mmy.year) as moc_name,
    dod.price as item_price, dod.created as created, dod.dispatched_on as dispatched_on, dto.payment_status as payment_status,
    dod.item_status, dod.dispatch_quantity as dispatch_quantity, dod.unitprice as unitprice, dod.cgst as cgst_amount, dod.price,
    dod.sgst as sgst_amount, dod.igst as igst_amount, pp.basepack_name as basepack_name, pp.basepack_code as basepack_code , pp.hsn_code as hsn_code, pp.cld_configurations,
    pp.cgst, pp.sgst, pp.igst,
    -- mod(dod.quantity, pp.cld_configurations) as quantity, div(dod.quantity, pp.cld_configurations) as cases,
    asse.code as shakti_enterpreneur_code,
    dod.net_amount as net_amount,
    CASE WHEN dod.dispatch_quantity > 0 THEN mod(dod.dispatch_quantity, pp.cld_configurations)
		ELSE mod(dod.quantity, pp.cld_configurations)
		END as quantity,
	CASE WHEN dod.dispatch_quantity > 0 THEN div(dod.dispatch_quantity, pp.cld_configurations)
		ELSE div(dod.quantity, pp.cld_configurations)
		END as cases
    FROM orders_distributororder as dto
    LEFT JOIN orders_distributororderdetail as dod ON (dod.distributor_order_id = dto.id)
    LEFT JOIN product_product as pp ON (pp.id = dod.product_id)
    LEFT JOIN app_alliancepartner as ap ON (ap.id = pp.brand_id)
    LEFT JOIN app_user as ause ON (ause.id = dto.shakti_enterpreneur_id)
    LEFT JOIN app_shaktientrepreneur as asse ON (ause.id = asse.user_id)
    LEFT JOIN app_user as aurd ON (aurd.id = dto.distributor_id)
    LEFT JOIN app_user as aua ON (aua.id = ap.user_id)
    LEFT JOIN app_regionaldistributor as ard ON (ard.user_id = dto.distributor_id)
    LEFT JOIN app_useraddress as dua ON (dua.id = dto.shipping_address_id)
    LEFT JOIN localization_state as lsa ON (lsa.id = dua.state_id)
    LEFT JOIN app_regionalsalespromoter as arsp ON (arsp.user_id = dto.sales_promoter_id)
    LEFT JOIN moc_mocmonth as mmm ON (mmm.id = dto.moc_id)
    LEFT JOIN moc_mocyear as mmy ON (mmy.id = mmm.moc_year_id)'''

    ALIANCE_ORDER_QUERY = '1'
    DISTRIBUTOR_ORDER_QUERY = '2'

    @staticmethod
    def dictfetchall(cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        if request_filter_list.get('order_type', None) == OrderAdvanceFilter.ALIANCE_ORDER_QUERY:
            sql, filters = OrderAdvanceFilter._get_alliance_sql(
                request_filter_list)
            queryset = AlliancePartnerOrder.objects.raw(sql, filters)

        else:
            sql, filters = OrderAdvanceFilter._get_distributor_sql(
                request_filter_list)
            queryset = DistributorOrder.objects.raw(sql, filters)

        return queryset

    @staticmethod
    def _get_alliance_sql(request_filter_list):
        start_amount = request_filter_list.get('start_amount', None)
        end_amount = request_filter_list.get('end_amount', None)
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        payment_status = request_filter_list.get('payment_status', None)
        order_status = request_filter_list.get('order_status_ap', None)

        filters = []
        sql = OrderAdvanceFilter._ALIANCE_FILTER_RAW_SQL
        sql += ' WHERE 1=1'
        if request_filter_list.get('order_number', None):
            sql += " and %s LIKE '%%' || apo.invoice_number || '%%' "
            filters.append('%' + request_filter_list.get('order_number') + '%')
        if request_filter_list.get('brand', None):
            sql += ' and apo.alliance_id = %s'
            filters.append(request_filter_list.get('brand'))

        if request_filter_list.getlist('redistribution_stockist', default=None):
            sql += ' and apo.distributor_id in %s'
            rs_ids = tuple([x.encode("utf-8")
                             for x in request_filter_list.getlist('redistribution_stockist')])
            filters.append(rs_ids)

        if start_amount:
            sql += ' and apod.price >= %s'
            filters.append(int(start_amount))
        if end_amount:
            sql += ' and apod.price <= %s'
            filters.append(int(end_amount))

        if start_date:
            sql += ' and apo.created::date >= %s'
            filters.append(start_date)
        if end_date:
            sql += ' and apo.created::date <= %s'
            filters.append(end_date)
        if order_status:
            sql += 'and order_status = %s '
            sql += 'and item_status = %s '
            filters.append(order_status)
            filters.append(order_status)
        if payment_status:
            sql += 'and payment_status = %s '
            filters.append(payment_status)

        if request_filter_list.getlist('moc', default=None):
            moc_ids = tuple([x.encode("utf-8")
                             for x in request_filter_list.getlist('moc')])
            sql += 'and apo.moc_id in %s '
            filters.append(moc_ids)

        sql += ' ORDER BY apo.id DESC'

        return sql, filters

    @staticmethod
    def _get_distributor_sql(request_filter_list):
        ''' get distributor sql '''
        start_amount = request_filter_list.get('start_amount', None)
        end_amount = request_filter_list.get('end_amount', None)
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        payment_status = request_filter_list.get('payment_status', None)
        order_status = request_filter_list.get('order_status', None)

        filters = []
        sql = OrderAdvanceFilter._DISTRIBUTOR_FILTER_RAW_SQL
        sql += ' WHERE 1=1'
        if request_filter_list.get('order_number', None):
            sql += " and %s LIKE '%%' || dto.invoice_number || '%%' "
            filters.append('%' + request_filter_list.get('order_number') + '%')
        if request_filter_list.get('brand', None):
            sql += ' and ap.user_id = %s'
            filters.append(request_filter_list.get('brand'))

        if request_filter_list.getlist('redistribution_stockist', default=None):
            sql += ' and dto.distributor_id in %s'
            rs_ids = tuple([x.encode("utf-8")
                             for x in request_filter_list.getlist('redistribution_stockist')])
            filters.append(rs_ids)

        if request_filter_list.getlist('sales_promoter', default=None):
            sql += ' and dto.sales_promoter_id in %s'
            rsp_ids = tuple([x.encode("utf-8")
                             for x in request_filter_list.getlist('sales_promoter')])
            filters.append(rsp_ids)

        if request_filter_list.getlist('shakti_enterpreneur', default=None):
            sql += ' and dto.shakti_enterpreneur_id in %s'
            shkti_ids = tuple([x.encode("utf-8")
                             for x in request_filter_list.getlist('shakti_enterpreneur')])
            filters.append(shkti_ids)

        if start_amount:
            sql += ' and dod.price >= %s'
            filters.append(int(start_amount))
        if end_amount:
            sql += ' and dod.price <= %s'
            filters.append(int(end_amount))

        if start_date:
            sql += ' and dod.created::date >= %s'
            filters.append(start_date)
        if end_date:
            sql += ' and dod.created::date <= %s'
            filters.append(end_date)
        if order_status:
            sql += 'and order_status = %s '
            sql += 'and item_status = %s '
            filters.append(order_status)
            filters.append(order_status)
        if payment_status:
            sql += 'and payment_status = %s '
            filters.append(payment_status)
        if request_filter_list.getlist('moc', default=None):
            moc_ids = tuple([x.encode("utf-8")
                             for x in request_filter_list.getlist('moc')])
            sql += 'and dto.moc_id in %s '
            filters.append(moc_ids)

        sql += ' ORDER BY dto.id DESC'

        return sql, filters


class SeLevelFilter(object):
    '''
    rse level filter
    '''
    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        order_queryset = SeLevelFilter._get_ordered_sql(request_filter_list)
        return order_queryset

    @staticmethod
    def _get_ordered_sql(request_filter_list):
        queryset = DistributorOrder.objects.filter()
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        mocs = request_filter_list.getlist('moc', default=None)
        states = request_filter_list.getlist('state', default=None)
        rss = request_filter_list.getlist('redistribution_stockist', default=None)
        ap = request_filter_list.get('alliance_partner', default=None)
        se = request_filter_list.get('shakti_enterpreneur', default=None)

        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(moc__in=moc_ids)
        if states:
            state_ids = tuple([x.encode("utf-8") for x in states])
            queryset = queryset.filter(shipping_address__state__in=state_ids)
        if ap:
            queryset = queryset.filter(distributor__regionaldistributor__alliance_partner__user=ap)
        if rss:
            rs_ids = tuple([x.encode("utf-8") for x in rss])
            queryset = queryset.filter(distributor__in=rs_ids)
        if se:
            queryset = queryset.filter(shakti_enterpreneur=se)
        

        data = queryset.values('distributor_order_details__distributor_order'
                               ).distinct().annotate(
            tamount=Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount'))
                         ),

            ordered=Case(When(order_status=OrderStatus.ORDERED,
                              then=F('total_amount'))),
            dispatched=Case(
                When(order_status=OrderStatus.DISPATCHED, then=F('total_amount'))),
            lines=Count(
                Case(When(order_status__in=[OrderStatus.DISPATCHED, OrderStatus.ORDERED], then=1),
                     output_field=CharField())
            ),
            orderedlines=Count(
                Case(When(order_status=OrderStatus.ORDERED, then=1),
                     output_field=CharField())
            ),
            dispatchedlines=Count(
                Case(When(order_status=OrderStatus.DISPATCHED, then=1),
                     output_field=CharField())
            ),
            moc_name=Concat('moc__name', Value('-'), 'moc__moc_year__year', output_field=CharField())
        ).values('tamount', 'ordered', 'dispatched', 'orderedlines', 'dispatchedlines', 'distributor__name', 'lines', 'sales_promoter__regionalsalespromoter__rsp_id',
                 'shakti_enterpreneur__name', 'shakti_enterpreneur__shakti_user__code', 'shipping_address__state__name', 'moc_name')

        return data


class BasepkLevelFilter(object):
    '''
    rse level filter
    '''
    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        order_queryset = BasepkLevelFilter._get_ordered_sql(
            request_filter_list)
        return order_queryset

    @staticmethod
    def _get_ordered_sql(request_filter_list):
        queryset = DistributorOrderDetail.objects.filter(
            distributor_order__sales_promoter__regionalsalespromoter__isnull=False,
            distributor_order__moc__isnull=False,
            net_amount__gt=0
        )
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        states = request_filter_list.getlist('state', default=None)
        mocs = request_filter_list.getlist('moc', default=None)
        alliance_partner = request_filter_list.get('alliance_partner', None)

        if alliance_partner:
            # queryset = queryset.filter(distributor_order__distributor__regionaldistributor__alliance_partner__user=alliance_partner)
            queryset = queryset.filter(product__brand__user=alliance_partner)
        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if states:
            state_ids = tuple([x.encode("utf-8") for x in states])
            queryset = queryset.filter(shipping_address__state__in=state_ids)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(distributor_order__moc__in=moc_ids)

        queryset = queryset.values('product__basepack_name', 'distributor_order__distributor__name',
                                   'distributor_order__sales_promoter__name',
                                   ).annotate(
            ordered_amount=Coalesce(Sum(
                Case(When(item_status=OrderStatus.ORDERED, then=F('net_amount')),
                     output_field=FloatField())
            ), 0),
            dispatched_amount=Coalesce(Sum(
                Case(When(item_status=OrderStatus.DISPATCHED, then=F('net_amount')),
                     output_field=FloatField())
            ), 0),
            grand_total=Coalesce(Sum(
                Case(When(item_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('net_amount')),
                     output_field=FloatField())
            ), 0),
            moc_name=Concat('distributor_order__moc__name', Value('-'), 'distributor_order__moc__moc_year__year', output_field=CharField())
        ).values('ordered_amount', 'distributor_order__distributor__name',
                 'dispatched_amount',
                 'grand_total', 'distributor_order__sales_promoter__regionalsalespromoter__rsp_id',
                 'product__basepack_name', 'shipping_address__state__name',
                 'moc_name',
                 ).order_by('shipping_address__state__name', 'distributor_order__moc')
        return queryset


class BasepkLevelFormatFilter(object):
    '''
    rse level filter
    '''
    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        order_queryset = BasepkLevelFormatFilter._get_ordered_sql(
            request_filter_list)
        return order_queryset

    @staticmethod
    def _get_ordered_sql(request_filter_list):
        queryset = DistributorOrderDetail.objects.filter()
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)

        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)

        return queryset.values('product__basepack_name'
                               ).annotate(tamount=Coalesce(Sum('net_amount'), 0)
                                          ).values('tamount',
                                                   'product__basepack_name',
                                                   )


class BillCountFilter(object):
    '''
    rse level filter
    '''
    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        order_queryset = BillCountFilter._get_ordered_sql(request_filter_list)
        return order_queryset

    @staticmethod
    def _get_ordered_sql(request_filter_list):
        queryset = DistributorOrder.objects.filter(moc__isnull=False)
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        states = request_filter_list.getlist('state', default=None)
        mocs = request_filter_list.getlist('moc', default=None)
        alliance_partner = request_filter_list.get('alliance_partner', None)

        if alliance_partner:
            queryset = queryset.filter(distributor__regionaldistributor__alliance_partner__user=alliance_partner)
            # queryset = queryset.filter(product__brand__user=alliance_partner)
        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if states:
            state_ids = tuple([x.encode("utf-8") for x in states])
            queryset = queryset.filter(shipping_address__state__in=state_ids)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(moc__in=moc_ids)

        queryset = queryset.values(
            'distributor_order_details__distributor_order'
        ).annotate(
            lines=Count('distributor_order_details__distributor_order')
        ).values(
            'lines'
        ).annotate(
            ordered_amount=Coalesce(Sum(
                Case(When(order_status=OrderStatus.ORDERED, then=F('distributor_order_details__net_amount')),
                     output_field=FloatField())
            ), 0),
            dispatched_amount=Coalesce(Sum(
                Case(When(order_status=OrderStatus.DISPATCHED, then=F('distributor_order_details__net_amount')),
                     output_field=FloatField())
            ), 0),
            tamount=Coalesce(Sum(
                Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('distributor_order_details__net_amount')),
                     output_field=FloatField())
            ), 0)
        ).values(
            'lines', 'tamount', 'ordered_amount', 'dispatched_amount'
        ).annotate(
            unique_prd=Count(
                'distributor_order_details__product', distinct=True)
        ).values(
            'tamount', 'lines', 'ordered_amount', 'dispatched_amount', 'unique_prd'
        ).annotate(
            billcount=Count('invoice_number', distinct=True),
            moc_name=Concat('moc__name', Value('-'), 'moc__moc_year__year', output_field=CharField())
        ).values(
            'unique_prd', 'billcount', 'tamount', 'ordered_amount',
            'distributor__name', 'lines', 'dispatched_amount',
            'sales_promoter__regionalsalespromoter__rsp_id',
            'sales_promoter__name', 'shakti_enterpreneur__name',
            'shakti_enterpreneur__shakti_user__code',
            'shipping_address__state__name', 'moc_name'
        )
        return queryset


class RsLevelFilter(object):
    '''
    rsp level filter
    '''
    @staticmethod
    def get_filtered_data(request_filter_list):
        ''' advanced filter logic '''
        sales_queryset = RsLevelFilter._get_ordered_sql(request_filter_list)
        eco_queryset, eco_count = RsLevelFilter._get_eco_sql(request_filter_list)
        return sales_queryset, eco_queryset, eco_count

    @staticmethod
    def _get_ordered_sql(request_filter_list):
        queryset = DistributorOrder.objects.filter(order_status__in=(1, 5))
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        distributor = request_filter_list.get('redistribution_stockist', None)
        mocs = request_filter_list.getlist('moc', default=None)

        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if distributor:
            queryset = queryset.filter(distributor_id=distributor)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(moc__in=moc_ids)

        return queryset.annotate(sales=Count('distributor_id')
                                 ).values('sales').annotate(
            ordered=Coalesce(Sum(
                Case(When(order_status=OrderStatus.ORDERED, then=F('total_amount')),
                     output_field=FloatField())
            ), 0),
            dispatched=Coalesce(Sum(
                Case(When(order_status=OrderStatus.DISPATCHED, then=F('total_amount')),
                     output_field=FloatField())
            ), 0),
            grandtotal=Coalesce(Sum(
                Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount')),
                     output_field=FloatField())
            ), 0),
            moc_name=Concat('moc__name', Value('-'), 'moc__moc_year__year', output_field=CharField())
        ).values('sales', 'ordered', 'dispatched', 'grandtotal', 'distributor__name', 'moc_name')

    # @staticmethod
    # def _get_eco_sql(request_filter_list):
    #     queryset = DistributorOrder.objects.filter(
    #         order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED))
    #     start_date = request_filter_list.get('start_date', None)
    #     end_date = request_filter_list.get('end_date', None)
    #     distributor = request_filter_list.get('redistribution_stockist', None)

    #     if start_date:
    #         queryset = queryset.filter(created__date__gte=start_date)
    #     if end_date:
    #         queryset = queryset.filter(created__date__lte=end_date)
    #     if distributor:
    #         queryset = queryset.filter(distributor_id=distributor)

    #     return queryset.annotate(sales=Count('shakti_enterpreneur_id', distinct=True)
    #                              ).values('sales').annotate(
    #         ordered=Count(
    #             Case(When(order_status=OrderStatus.ORDERED, then=F('total_amount')),
    #                  output_field=FloatField())
    #         ),
    #         dispatched=Count(
    #             Case(When(order_status=OrderStatus.DISPATCHED, then=F('total_amount')),
    #                  output_field=FloatField())
    #         ),
    #         grandtotal=Count(
    #             Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount')),
    #                  output_field=FloatField())
    #         )
    #     ).values('sales', 'ordered', 'dispatched', 'grandtotal', 'distributor__name')
    @staticmethod
    def _get_eco_sql(request_filter_list):
        queryset = DistributorOrder.objects.filter(
            order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED))
        start_date = request_filter_list.get('start_date', None)
        end_date = request_filter_list.get('end_date', None)
        distributor = request_filter_list.get('redistribution_stockist', None)
        mocs = request_filter_list.getlist('moc', default=None)

        if start_date:
            queryset = queryset.filter(created__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created__date__lte=end_date)
        if distributor:
            queryset = queryset.filter(distributor_id=distributor)
        if mocs:
            moc_ids = tuple([x.encode("utf-8") for x in mocs])
            queryset = queryset.filter(moc__in=moc_ids)

        queryset = queryset.values(
            'shakti_enterpreneur_id'
        ).annotate(
            sales=Count('shakti_enterpreneur_id', distinct=True)
        )

        eco_count = queryset.aggregate(eco_count = Sum('sales'))['eco_count'] or 0
        queryset = queryset.values('shakti_enterpreneur_id', 'sales').annotate(
            ordered=Count(
                Case(When(order_status=OrderStatus.ORDERED, then=F('total_amount')),
                     output_field=FloatField())
            ),
            dispatched=Count(
                Case(When(order_status=OrderStatus.DISPATCHED, then=F('total_amount')),
                     output_field=FloatField())
            ),
            grandtotal=Count(
                Case(When(order_status__in=(OrderStatus.ORDERED, OrderStatus.DISPATCHED), then=F('total_amount')),
                     output_field=FloatField())),
            moc_name=Concat('moc__name', Value('-'), 'moc__moc_year__year', output_field=CharField())
        ).values(
            'shakti_enterpreneur_id', 'sales', 'ordered', 'dispatched', 'grandtotal', 'distributor__name', 'sales_promoter__name', 'shakti_enterpreneur__shakti_user__code', 'moc_name'
        ).order_by(
            'distributor__name', 'shakti_enterpreneur__name'
        )
        return queryset, eco_count
