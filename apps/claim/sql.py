''' claim/sql.py '''
from django.db import connection
from django.utils import timezone as dt

from claim.models import Claim
from misreporting.sql import OrderAdvanceFilter
from hul.choices import OrderStatus


class ClaimDetail(object):

    _CLAIM_PRODUCT_DETAILS = '''
        select apd.id, dbo.shakti_enterpreneur_id,  sum(dod.discount_amount) as discount_amount, sum(dod.price) as ordered_amount, pr.basepack_name,
        pr.basepack_code, shakti.name as shakti_name, apd.invoice_number, alliance.name as alliance, distributor.name as distributor, dod.promotion_applied as offer,
        to_char(to_timestamp (date_part('month', date_trunc('day', apd.created - interval '1 month'))::text, 'MM'), 'Month') as settlement_month,
        date_part('year', date_trunc('day', apd.created - interval '1 month'))::text as settlement_year,
        shakti_enter.code, apd.claim_status
        from orders_alliancepartnerdiscountdetail as apdd
        inner join orders_alliancepartnerorder as apd on apdd.alliance_partner_order_id = apd.id
        inner join orders_distributororder as dbo on apd.distributor_id = dbo.distributor_id
        inner join orders_distributororderdetail as dod on dbo.id = dod.distributor_order_id and dod.product_id=apdd.product_id and dod.discount_amount > 0 and dod.item_status={item_status} and to_char(dod.dispatched_on, 'MM-YYYY') = '{claim_month}'
        inner join product_product as pr on dod.product_id=pr.id
        inner join app_user as shakti on dbo.shakti_enterpreneur_id = shakti.id
        inner join app_shaktientrepreneur as shakti_enter on dbo.shakti_enterpreneur_id = shakti_enter.user_id
        inner join app_user as alliance on apd.alliance_id = alliance.id
        inner join app_user as distributor on apd.distributor_id = distributor.id
        where apdd.alliance_partner_order_id={order_id}
        group by dbo.shakti_enterpreneur_id, pr.id, shakti.id, apd.id, alliance.id, distributor.id, dod.promotion_applied, shakti_enter.code

    '''

    @staticmethod
    def get_claim_detail(order_id):
        cursor = connection.cursor()

        today = dt.now()
        prev_month = (today.replace(day=1) - dt.timedelta(days=1))
        sql = ClaimDetail._CLAIM_PRODUCT_DETAILS.format(
            order_id=order_id, item_status=OrderStatus.DISPATCHED,
            claim_month=prev_month.strftime('%m-%Y'))

        cursor.execute(sql)
        queryset = OrderAdvanceFilter.dictfetchall(cursor)
        return queryset
