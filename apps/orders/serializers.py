''' orders/serializer.py '''
from rest_framework import serializers
from orders.models import (DistributorOrder, DistributorOrderDetail,
                           DistributorStock, AlliancePartnerOrder,
                           AlliancePartnerOrderDetail)
from product.models import Product
from app.serializers import AlliancePartnerSerializer, ShaktiEntrepreneurUserSerializer
from localization.serializers import MeasurementUnitSerializer
from offers.models import Promotions, PromotionLines


class ProductSerializer(serializers.ModelSerializer):
    '''
    serializer to get product details
    '''
    brand = AlliancePartnerSerializer(read_only=True)

    class Meta:
        '''
        meta class for Products
        '''
        unit = MeasurementUnitSerializer(many=False)
        model = Product
        fields = ('id', 'basepack_name', 'basepack_code', 'basepack_size', 'unit',
                  'sku_code', 'expiry_day', 'cld_configurations', 'cld_rate',
                  'mrp', 'tur', 'net_rate', 'brand', 'image')

    def to_representation(self, instance):
        result = super(
            ProductSerializer, self).to_representation(instance)
        if result:
            unit = result.get('unit', None)
            result['unit'] = unit
        return result


class AlliancePartnerOrderSerializer(serializers.ModelSerializer):
    '''
    serializer for AlliancePartnerOrder
    '''
    class Meta:
        '''
        meta class for AlliancePartnerOrder
        '''
        model = AlliancePartnerOrder
        fields = '__all__'


class AlliancePartnerOrderDetailSerializer(serializers.ModelSerializer):
    '''
    serializer for AlliancePartnerOrderDetail
    '''
    class Meta:
        '''
        meta class for AlliancePartnerOrderDetail
        '''
        model = AlliancePartnerOrderDetail
        fields = '__all__'


class DistributorOrderDetailProductSerializer(serializers.ModelSerializer):
    '''
    serializer for placing distributor order from app
    '''
    product = ProductSerializer(read_only=True)
    promotion = serializers.SerializerMethodField()

    class Meta:
        ''' meta class for PlaceDistributorOrderSerializer '''
        model = DistributorOrderDetail
        fields = '__all__'

    def get_promotion(self, obj):

        return PromotionLines.objects.filter(pk__in=obj.promotion).values('free_product_id',
                                                                          'free_quantity', 'discount', 'buy_product_id', 'buy_quantity')


class DistributorOrderDetailSerializer(serializers.ModelSerializer):
    '''
    serializer for placing distributor order from app
    '''
    class Meta:
        ''' meta class for PlaceDistributorOrderSerializer '''
        model = DistributorOrderDetail
        fields = '__all__'


class DistributorOrderSerializer(serializers.ModelSerializer):
    '''
    Distributor Order Serializer
    '''
    products = DistributorOrderDetailSerializer(many=True)

    class Meta:
        model = DistributorOrder
        fields = ('distributor', 'sales_promoter', 'shakti_enterpreneur',
                  'shipping_address', 'amount', 'tax', 'total_amount',
                  'products', 'discount_amount')

    def create(self, validated_data):
        ''' create method for placing order from API '''
        products_data = validated_data.pop('products')
        order = DistributorOrder.objects.create(**validated_data)
        for product_data in products_data:
            product_data['distributor_order'] = order
            DistributorOrderDetail.objects.create(**product_data)
        return order


class RspOrdersSerializer(serializers.ModelSerializer):
    '''
    Rsp Orders Serializer
    '''
    distributor_order_details = DistributorOrderDetailProductSerializer(
        many=True, read_only=True)
    shakti_enterpreneur = ShaktiEntrepreneurUserSerializer(read_only=True)

    class Meta:
        model = DistributorOrder
        fields = ('id', 'distributor', 'sales_promoter', 'shakti_enterpreneur', 'shipping_address',
                  'amount', 'total_amount', 'invoice_number', 'order_status', 'payment_status',
                  'distributor_order_details', 'discount_amount')

    def to_representation(self, instance):
        result = super(
            RspOrdersSerializer, self).to_representation(instance)
        if result:
            order_details = result.get('distributor_order_details', None)
            shakti_enterpreneur = result.get('shakti_enterpreneur', None)
            shakti_user = shakti_enterpreneur.pop('shakti_user')
            shakti_enterpreneur['code'] = shakti_user.get('code')

            for order in order_details:
                product = order.get('product', None)
                brand = product.get('brand', None)
                brand_data = {}
                brand_data['id'] = brand.get('id', None)
                user = brand.get('user', None)
                brand_data['name'] = user.get('name', None)
                brand_data['code'] = brand.get('code', None)
                order['stockist_margin'] = brand.get(
                    'stockist_margin', None)
                product['brand'] = brand_data
        return result


class DistributorStockSerializer(serializers.ModelSerializer):
    '''
    serializer for placing distributor order from app
    '''
    class Meta:
        ''' meta class for PlaceDistributorOrderSerializer '''
        model = DistributorStock
        fields = '__all__'
