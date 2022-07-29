from .models import AlliancePartnerOrder, AlliancePartnerOrderDetail
from hul.choices import OrderStatus

class UpdatePrimaryOrders(object):
    
    def update_primary_orders(self):
        import pdb; pdb.set_trace()
        orders = AlliancePartnerOrder.objects.filter(id__in=(138,140,141,142,144,145,146,147,148,149,150,151,152,153,155,156,157,159,160,161,162,163,164,166,167,168,169,171,172,173,174,175,176,177,178,179,180,181,183,184,185,186,187,188,189,190,191,193,194,195,197,198,199,200,201,202,203,204,205,206,207,208,209,210,212,213,214,215,216,218,285))
        for order in orders:
            total_tax = 0
            total_amount = 0
            amount = 0
            lines = order.alliancepartnerorderdetail_set.get_queryset()
            for line in lines:
                product = line.product
                line.unitprice = product.base_rate
                line.cgst = product.cgst
                line.sgst = product.sgst
                line.igst = product.igst
                
                quantity = line.dispatch_quantity if line.dispatch_quantity else line.quantity
                
                taxable_amount = line.unitprice * quantity
                line.cgst_amount = round(float(taxable_amount) * float(line.cgst) / 100.0, 2)
                line.sgst_amount = round(float(taxable_amount) * float(line.sgst) / 100.0, 2)
                line.igst_amount = round(float(taxable_amount) * float(line.igst) / 100.0, 2)

                line.price = taxable_amount
                if line.item_status != OrderStatus.CANCELLED:
                        
                    amount += taxable_amount 
                    total_amount += line.price + line.cgst_amount + line.sgst_amount + line.igst_amount
                    total_tax += line.cgst_amount + line.sgst_amount + line.igst_amount
                
                print (line.product, '--', line.unitprice, '--', product.base_rate)
                line.save()

            print (order.amount, '--', amount)
            order.amount = round(amount, 2)
            order.tax = round(total_tax, 2)
            order.total_amount = round(total_amount, 2)
            order.save()

           
        return 