'''Api.py for Products/Category Models'''
from rest_framework import generics, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils import timezone

from hul.utility import HulUtility
from hul.messages import Messages
from hul.constants import (PRODUCT_LIST_SIZE, HTTP_USER_ERROR,
                           SUCCESS_MESSAGE_KEY, MESSAGE_KEY)

from app.models import RegionalDistributor, RegionalSalesPromoter, ShaktiEntrepreneur
from product.serializers import ProductSerializer, CategorySerializer
from product.models import Category, Product
#=========================================================================
# List Products Api
#=========================================================================


class Products(generics.ListAPIView):
    '''
    API for Change Password
    '''
    serializer_class = ProductSerializer
    queryset = Product.objects.filter(is_active=True)

    def get(self, request):

        if request.user:
            brand_id = int(request.GET.get('brand', 0))
            search = request.GET.get('search', None)
            categories = request.GET.get('categories', None)
            price_order = request.GET.get('price_order', None)
            shakti_id = request.GET.get('shakti_enterpreneur', None)

            sales_promoter = RegionalSalesPromoter.objects.filter(user=request.user
                                                                  ).select_related('regional_distributor').first()

            if sales_promoter:
                regional_distributor = sales_promoter.regional_distributor.pk
            else:
                regional_distributor = shakti_enterpreneur.regional_sales.regional_distributor_id

            alliance_partners = RegionalDistributor.objects.select_related('user').values('alliance_partner', 'alliance_partner__user').\
                filter(pk=regional_distributor, is_active=True)
            brand_ids = [alliance['alliance_partner']
                         for alliance in alliance_partners]

            brands = ','.join(map(str, brand_ids))
            if brand_id is not 0 and len(brands) > 0:
                brand_list = [brand_id]
                rec = set(brand_list) & set(brand_ids)
                brands = ','.join(map(str, rec))

            brands = map(int, brands.split(','))
            product_list = Product.objects.filter(
                brand_id__in=brands, is_active=True)

            if search is not None:
                product_list = product_list.filter(
                    Q(category__name__icontains=search) |
                    Q(brand__code__icontains=search) |
                    Q(partner_code__icontains=search) |
                    Q(basepack_name__icontains=search) |
                    Q(basepack_code__icontains=search) |
                    Q(basepack_size__icontains=search) |
                    Q(sku_code__icontains=search)
                )
            if categories not in [None, '0']:
                categories = categories.split(",")
                product_list = product_list.filter(category_id__in=categories)

            if price_order is not None:
                if price_order == '1':
                    product_list = product_list.order_by('tur','id')
                elif price_order == '2':
                    product_list = product_list.order_by('-tur', 'id')
                else:
                    product_list = product_list.order_by('-id')
            else:
                product_list.order_by('-id')

            paginator = Paginator(product_list, PRODUCT_LIST_SIZE)

            try:
                product_list = paginator.page(request.GET.get('page', None))
            except PageNotAnInteger:
                product_list = paginator.page(1)
            except EmptyPage:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
                return Response(response_data, status=status.HTTP_200_OK)

            response = {}
            response_data = {}

            serializer = ProductSerializer(
                product_list, many=True, context={'request': request,
                                                  'shakti_enterpreneur': shakti_id})

            if serializer.data:
                response = serializer.data
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        return Response(response_data, status=status.HTTP_200_OK)

#=========================================================================
# List Categories Api
#=========================================================================


class ProductCategory(generics.ListAPIView):
    '''
    API for Category
    '''
    serializer_class = CategorySerializer

    @classmethod
    def get(cls, request):
        '''
        Return all Categories
        '''
        if request.user:
            category_list = Category.objects.filter(
                is_active=True).order_by('-id')

            response = {}
            response_data = {}

            serializer = CategorySerializer(category_list, many=True)

            if serializer.data:
                response = serializer.data
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        return Response(response_data, status=status.HTTP_200_OK)
