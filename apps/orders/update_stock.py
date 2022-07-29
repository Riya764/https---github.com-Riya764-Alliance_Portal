from orders.models import DistributorStock
from django.utils import timezone

class UpdateDistributorStock(object):
    from_date = timezone.now().date().replace(day=3, month=10)
    to_date = timezone.now().date().replace(day=14, month=10)
    
    def update_stock(self):

        stocks = DistributorStock.objects.filter(created__date=self.from_date)
        for stock in stocks:
            print(stock.distributor_id, stock.product_id)
            DistributorStock.objects.filter(created__date__lte=self.to_date, created__date__gt=self.from_date,distributor_id=stock.distributor_id, product_id=stock.product_id
                            ).update(opening_stock=stock.opening_stock, closing_stock=stock.closing_stock, amount=stock.amount)


    def update_dates(self):
        stocks = DistributorStock.objects.all().order_by('-created')
        for stock in stocks:
            print(stock.distributor_id, stock.product_id)
            print("---", stock.created, stock.modified)
            stock.modified=stock.created
            print("---", stock.created, stock.modified)
            stock.save()