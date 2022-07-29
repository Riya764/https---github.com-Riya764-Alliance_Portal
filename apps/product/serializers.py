''' Serializers.py '''
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.utils import timezone
from django.db.models import Q

from product.models import Category, Product, ProductImages
from offers.models import Promotions, PromotionLines
from app.serializers import AlliancePartnerSerializer
from localization.serializers import MeasurementUnitSerializer


class ProductImagesSerializer(serializers.ModelSerializer):
    '''
    Serializer to return Product Images
    '''
    class Meta:
        model = ProductImages
        fields = ('image', 'sort_order')


class CategorySerializer(serializers.ModelSerializer):
    '''
    Category Serializer
    '''
    class Meta:
        model = Category
        fields = ('id', 'name',)


class ProductDetailSerializer(serializers.ModelSerializer):
    '''
    Product detail Serializer
    '''
    class Meta:
        model = Product
        fields = ('id', 'basepack_name',)


class ProductSerializer(serializers.ModelSerializer):
    '''
    Product Serializer
    '''
    category = CategorySerializer(many=False)
    unit = MeasurementUnitSerializer(many=False)
    brand = AlliancePartnerSerializer(many=False)
    offers = serializers.SerializerMethodField()
    images = SerializerMethodField('get_product_images')

    class Meta(object):
        model = Product
        fields = ('id', 'category', 'brand', 'partner_code', 'basepack_name',
                  'basepack_code', 'basepack_size', 'unit', 'sku_code', 'offers',
                  'cld_configurations', 'cld_rate', 'mrp', 'tur', 'net_rate',
                  'base_rate', 'cgst', 'sgst', 'igst',
                  'image', 'images')

    def get_offers(self, obj):
        shakti_id = self.context['shakti_enterpreneur']

        return obj.offers_promotionlines_related.filter(
            promotion__end__gte=timezone.now()).exclude(
                promotion__start__gt=timezone.now().today()).filter(
            Q(promotion__shakti_enterpreneur=shakti_id) |
            Q(promotion__shakti_enterpreneur=None)).values(
            'buy_quantity', 'free_product', 'free_product__basepack_name',
            'free_quantity', 'discount', 'promotion', 'id'
        )

    def to_representation(self, instance):
        result = super(
            ProductSerializer, self).to_representation(instance)

        if result:
            unit = result.get('unit', None)
            brand = result.get('brand', None)
            brand_data = {}
            brand_data['id'] = brand.get('id', None)
            user = brand.get('user', None)
            brand_data['name'] = user.get('name', None)
            brand_data['code'] = brand.get('code', None)
            result['stockist_margin'] = brand.get('stockist_margin', None)
            result['brand'] = brand_data
            result['unit'] = unit.get('unit', None)
        return result

    @staticmethod
    def get_product_images(product):
        '''
        Return product images
        '''
        product_images = ProductImages.objects.filter(product_id=product.id,
                                                      is_active=True).order_by('sort_order')[:5]
        serializer = ProductImagesSerializer(product_images, many=True)
        return serializer.data
