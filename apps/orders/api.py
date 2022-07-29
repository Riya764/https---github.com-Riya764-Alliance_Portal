''' orders/api.py '''
import json
from rest_framework import generics, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage

from hul.utility import HulUtility
from hul.messages import Messages
from hul.constants import (HTTP_USER_ERROR, MESSAGE_KEY,
                           SUCCESS_MESSAGE_KEY, ORDER_LIST_SIZE)
from hul.choices import OrderStatus, CancelOrderReasons
from app.models import ShaktiEntrepreneur
from orders.models import (DistributorOrder, DistributorOrderDetail)
from orders.lib.order_management import OrderManagement
from orders.serializers import (
    DistributorOrderSerializer, RspOrdersSerializer)


#=========================================================================
# Place order Api
#=========================================================================


class Orders(generics.ListCreateAPIView):
    '''
    API for order creation and order history
    '''
    queryset = DistributorOrder.objects.all()
    serializer_class = DistributorOrderSerializer

    def post(self, request, *args, **kwargs):
        ''' place order '''
        user = request.user
        response = {}
        response_data = {}
        if user.id:
            try:
                order_mgmt_obj = OrderManagement()
                valid_units = order_mgmt_obj.validate_units(request.data)
                if not valid_units:
                    response_data = HulUtility.data_wrapper(
                        status_code=HTTP_USER_ERROR)
                    response_data[MESSAGE_KEY] = Messages.VALID_UNIT
                    return Response(response_data, status=status.HTTP_200_OK)
               
                order_mgmt_obj.prepare_distributor_order(request.data)

                distributor_serializer = DistributorOrderSerializer(
                    data=request.data)
                if distributor_serializer.is_valid():
                    do_id = distributor_serializer.save()
                    response['message'] = Messages.ORDER_PLACED
                    response['order_id'] = do_id.id
                    response['total_amount'] = do_id.total_amount
                    response_data = HulUtility.data_wrapper(
                        response, message=SUCCESS_MESSAGE_KEY)
                else:
                    error = distributor_serializer.errors
                    response_data = HulUtility.data_wrapper(
                        status_code=HTTP_USER_ERROR)
                    response_data[MESSAGE_KEY] = json.dumps(error)
            except StandardError as exp:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = exp.message
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request):
        '''update order status'''
        response_data = {}

        # condition when shakti login
        rsp_id = request.user.id
        rsp = ShaktiEntrepreneur.objects.filter(user_id=rsp_id).first()
        if rsp:
            rsp_id = rsp.regional_sales.user_id

        order_detail = DistributorOrder.objects.filter(pk=request.data.get('order', None),
                                                       sales_promoter_id=rsp_id).first()
        if order_detail:
            if order_detail.order_status == OrderStatus.ORDERED:
                DistributorOrder.objects.filter(pk=request.data.get('order', None),
                                                sales_promoter=rsp_id).update(order_status=OrderStatus.CANCELLED,
                                                                              cancel_order=CancelOrderReasons.SHAKTICANCEL)
                DistributorOrderDetail.objects.filter(distributor_order=request.data.get(
                    'order', None)).update(item_status=OrderStatus.CANCELLED)
                response = ''
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
            else:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.ORDER_CANCEL
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND

        return Response(response_data, status=status.HTTP_200_OK)

    @classmethod
    def get(cls, request):
        ''' get request type for a API '''
        user = request.user
        page = request.GET.get('page', 1)
        shakti_enterpreneur = request.GET.get('shakti_enterpreneur', 0)
        month = request.GET.get('month', 0)
        year = request.GET.get('year', 0)
        if user.id:
            shakti_user = ShaktiEntrepreneur.objects.filter(
                user_id=user.id).first()
            if shakti_user:
                order_list = DistributorOrder.objects.filter(
                    shakti_enterpreneur=user).order_by('-created')
            else:
                order_list = DistributorOrder.objects.filter(
                    sales_promoter=user).order_by('-created')

            if shakti_enterpreneur != '0':
                shakti_enterpreneur = map(int, shakti_enterpreneur.split(','))
                order_list = order_list.filter(
                    shakti_enterpreneur__in=shakti_enterpreneur)
            if month != '0':
                where = 'EXTRACT(\'month\' FROM created) = %(month)s' % \
                    {'month': month}
                order_list = order_list.extra(where=[where])
            if year != '0':
                where = 'EXTRACT(\'year\' FROM created) = %(year)s' % \
                    {'year': year}
                order_list = order_list.extra(where=[where])

            paginator = Paginator(order_list, ORDER_LIST_SIZE)

            try:
                order_list = paginator.page(page)
            except EmptyPage:
                response_data = HulUtility.data_wrapper(
                    status_code=HTTP_USER_ERROR)
                response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
                return Response(response_data, status=status.HTTP_200_OK)

            serializer = RspOrdersSerializer(order_list, many=True)
            response_data = {}
            response = {}
            if serializer.data:
                response = serializer.data
                response_data = HulUtility.data_wrapper(
                    response, message=SUCCESS_MESSAGE_KEY)
        else:
            response_data = HulUtility.data_wrapper(
                status_code=HTTP_USER_ERROR)
            response_data[MESSAGE_KEY] = Messages.NO_RECORD_FOUND
        return Response(response_data, status=status.HTTP_200_OK)
