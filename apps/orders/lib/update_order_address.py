from orders.models import DistributorOrder, DistributorOrderDetail
from app.models import ShaktiEntrepreneur


class UpdateAddress(object):

    @staticmethod
    def update_address():
        unique_shaktis = DistributorOrder.objects.values_list('shakti_enterpreneur__id', flat=True).distinct(
            'shakti_enterpreneur').order_by('shakti_enterpreneur__id')

        for shakti in unique_shaktis:
            shakti_obj = ShaktiEntrepreneur.objects.filter(
                user_id=shakti).first()

            if shakti_obj:
                secondary_orders = DistributorOrder.objects.filter(
                    shakti_enterpreneur_id=shakti)
                secondary_orders.update(
                    shipping_address_id=shakti_obj.address_id)

                DistributorOrderDetail.objects.filter(distributor_order__in=secondary_orders).update(
                    shipping_address_id=shakti_obj.address_id)
                print('Updated Order Address for Shakti: ' +
                      shakti_obj.code or shakti_obj.user.get_full_name())
                print('in orders : ')
                for order in secondary_orders:
                    print(order.id)
