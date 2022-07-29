''' Form '''

from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from app.models import (AlliancePartner, RegionalDistributor,
                        ShaktiEntrepreneur, RegionalSalesPromoter, UserAddress)
from .models import AlliancePartnerOrderDetail, DistributorStock
from orders.models import DistributorOrder, AlliancePartnerOrder, DistributorOrderDetail,DistributorStock

from orders.order_status_choices import OrderStatusChoices
from product.models import Product
from hul.widgets import SelectWithDisabled
from hul.choices import OrderType, PriceRange, OrderStatus


class DistributorOrderAdminForm(forms.ModelForm):
    ''' order admin form for distributor orders '''
    # returned_units=forms.IntegerField()
    class Meta:
        model = DistributorOrder
        fields = []

    def __init__(self, *args, **kwargs):
        super(DistributorOrderAdminForm, self).__init__(*args, **kwargs)

        order_instance = self.instance
        status_obj = OrderStatusChoices()
        # print(self.fields['product'][0] ,'******')
        if order_instance.id and 'order_status' in self.fields:
            status_choices = status_obj.get_disabled_choices(
                order_instance.order_status,
                OrderStatus.STATUS)
            self.fields['order_status'] = forms.ChoiceField(choices=status_choices,
                                                            widget=SelectWithDisabled)

        if order_instance.id and 'item_status' in self.fields:
            status_choices = status_obj.get_disabled_choices(
                order_instance.item_status,
                OrderStatus.STATUS)
            self.fields['item_status'] = forms.ChoiceField(choices=status_choices,
                                                           widget=SelectWithDisabled)
    
        # if  order_instance.order_status==5:
        #     print('*********')
        #     self.base_fields["return_order"].widget = forms.CheckboxInput()
            
        #     # self.fields.remove('return_order')
        # else:
        #    self.base_fields['return_order'].disabled = True
        #    self.base_fields['return_order'].widget = forms.HiddenInput()
             



        self.fields['product'].queryset = DistributorOrderDetail.objects.filter(distributor_order_id=order_instance.id).select_related('product')
        # self.fields['product'].widget.choices = self.fields['product'].choices
    # # product = forms.ModelChoiceField(queryset = Product.objects.all())
    #         self.fields['return_units']=forms.IntegerField(required=False)
    #         self.fields['return_order']=forms.BooleanField()
    
    # product = forms.ModelChoiceField(queryset = DistributorOrderDetail.objects.filter(distributor_order=order_instance).
    #         select_related('product'))
    product = forms.ModelChoiceField(queryset = DistributorOrderDetail.objects.none())
    return_units=forms.IntegerField(required=False)
    return_order=forms.BooleanField()





class AllianceOrderAdminForm(forms.ModelForm):
    ''' order admin form for distributor orders '''
    class Meta:
        model = AlliancePartnerOrder
        fields = []

    def __init__(self, *args, **kwargs):
        super(AllianceOrderAdminForm, self).__init__(*args, **kwargs)

        order_instance = self.instance
        status_obj = OrderStatusChoices()

        if order_instance.id and 'order_status' in self.fields:
            status_choices = status_obj.get_disabled_choices(
                order_instance.order_status,
                OrderStatus.APSTATUS, 'primary')
            self.fields['order_status'] = forms.ChoiceField(choices=status_choices,
                                                            widget=SelectWithDisabled)

        if order_instance.id and 'item_status' in self.fields:
            status_choices = status_obj.get_disabled_choices(
                order_instance.item_status,
                OrderStatus.APSTATUS, 'primary')
            self.fields['item_status'] = forms.ChoiceField(choices=status_choices,
                                                           widget=SelectWithDisabled)


class DistributorOrderDetailAdminForm(forms.ModelForm):
    ''' order admin form for distributor orders '''
    class Meta:
        model = DistributorOrderDetail
        fields = []

    def __init__(self, *args, **kwargs):
        super(DistributorOrderDetailAdminForm, self).__init__(*args, **kwargs)

        # self.fields['product'].queryset = Product.objects.all(
        # ).select_related('brand', 'brand__address__country', 'brand__address__state')
  

    # def save(self, commit=True):
    #     product = self.cleaned_data.get('product', None)
    #     price = self.cleaned_data.get('price', None)
    #     ordered_units = self.cleaned_data.get('ordered_units', None)
    #     # distributor=self.cleaned_data.get('distributor0')
      
       
    #     reg=DistributorStock.objects.filter(product=product)
    #     reg[0].closing_stock+=ordered_units
    #     print(ordered_units)
    #     reg[0].save()


        # ...do something with extra_field here...
        # return super(DistributorOrderAdminForm, self).save(commit=commit)