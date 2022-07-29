from app.models import User, RegionalDistributor
from hul.choices import OrderDay


def getstockist(request):
    stockist = False
    order_day = None
    if request.user:
        groups = request.user.groups.all().values_list('name', flat=True)
        if 'Distributor' in groups:
            distributor = RegionalDistributor.objects.filter(
                user=request.user).first()
            order_day = OrderDay.LABEL[distributor.order_day]
            stockist = True
    return {'stockist': stockist, 'order_day': order_day}
