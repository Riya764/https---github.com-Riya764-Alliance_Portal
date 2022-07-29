from moc.models import MoCMonth
from orders.models import DistributorOrder, AlliancePartnerOrder


class UpdateOrdersMoC(object):

    @staticmethod
    def get_mocs():
        mocs = MoCMonth.objects.all()
        return mocs

    @staticmethod
    def update_primary_orders():
        mocs = UpdateOrdersMoC.get_mocs()
        for moc in mocs:
            AlliancePartnerOrder.objects.filter(
                created__gte=moc.start_date, created__lte=moc.end_date).update(moc=moc)

    @staticmethod
    def update_secondary_orders():
        mocs = UpdateOrdersMoC.get_mocs()
        for moc in mocs:
            DistributorOrder.objects.filter(
                created__gte=moc.start_date, created__lte=moc.end_date).update(moc=moc)
