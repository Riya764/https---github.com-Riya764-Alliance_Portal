''' Serializers.py '''
import datetime
from rest_framework import serializers
from oauth2_provider.models import AccessToken
from app.models import User, UserAddress, AlliancePartner, ShaktiEntrepreneur
from orders.models import DistributorOrder
from offers.models import ShaktiBonusAllLines
from localization.serializers import CitySerializer, StateSerializer


class UserSerializer(serializers.ModelSerializer):
    '''
    serializer for update user
    '''
    class Meta(object):
        '''
        meta for user
        '''
        model = User
        fields = ('id', 'name', 'username', 'email', 'image', 'contact_number')
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
        }

    @classmethod
    def create(cls, validated_data):
        return User.objects.create_user(**validated_data)


class AccessTokenSerializer(serializers.ModelSerializer):
    '''
    Serializer for Access Token
    '''
    class Meta(object):
        '''
        meta for access token
        '''
        model = AccessToken
        fields = ('token',)


class UserAddressSerializer(serializers.ModelSerializer):
    '''
    serializer for update user
    '''
    city = CitySerializer(many=False)
    state = StateSerializer(many=False)

    class Meta(object):
        '''
        meta for user
        '''
        model = UserAddress
        fields = ('id', 'address_line1', 'address_line2',
                  'address_line3', 'city', 'state', 'post_code')


class AlliancePartnerSerializer(serializers.ModelSerializer):
    '''
    serializer for Alliance Partner
    '''
    user = UserSerializer(many=False)

    class Meta(object):
        '''
        meta for user
        '''
        model = AlliancePartner
        fields = ('id', 'user', 'code', 'stockist_margin')


class ShaktiEntrepreneurSerializer(serializers.ModelSerializer):
    '''
    serializer for update user
    '''
    user = UserSerializer(many=False)
    address = UserAddressSerializer(many=False)
    bonus = serializers.SerializerMethodField()
    distributoroffers = serializers.SerializerMethodField()

    class Meta(object):
        '''
        meta for user
        '''
        model = ShaktiEntrepreneur
        fields = ('id', 'address', 'user', 'regional_sales',
                  'code', 'beat_name', 'order_day', 'bonus', 'distributoroffers',
                  'min_order')

    def get_bonus(self, obj):
        shaktibonus = []

        if hasattr(obj, 'shaktibonus'):
            if obj.shaktibonus.end >= datetime.date.today():
                shaktibonus = obj.shaktibonus.shaktibonuslines_set.values(
                    'target_amount', 'discount_type', 'discount')
        if not shaktibonus:
            shaktibonus = ShaktiBonusAllLines.objects.filter(
                shakti_bonus__end__gte=datetime.date.today(),
                shakti_bonus__shakti_enterpreneur__isnull=True).values(
                'target_amount', 'discount_type', 'discount')

        return shaktibonus

    def get_distributoroffers(self, obj):
        distributoroffers = None
        if hasattr(obj.regional_sales.regional_distributor, 'distributoroffers'):
            distributoroffers = {}
            offers = obj.regional_sales.regional_distributor.distributoroffers

            if offers.start <= datetime.date.today() and offers.end >= datetime.date.today():
                distributoroffers['discount_type'] = offers.discount_type
                distributoroffers['discount'] = offers.discount
                distributoroffers['id'] = offers.id

        return distributoroffers

    def to_representation(self, instance):
        result = super(ShaktiEntrepreneurSerializer,
                       self).to_representation(instance)
        if result:
            shakti_user = result.get('user', None)
            if shakti_user:
                date = datetime.date.today()
                start_week = date - datetime.timedelta(date.weekday())
                end_week = start_week + datetime.timedelta(7)

                order_count = DistributorOrder.objects.filter(shakti_enterpreneur_id=shakti_user.get(
                    'id', None), is_active=True, created__range=[start_week, end_week]).count()
                result['order_count'] = order_count
        return result


class ShaktiEntrepreneurDetailsSerializer(serializers.ModelSerializer):
    '''
    serializer Shakti details from user id
    '''
    class Meta(object):
        '''
        meta for user
        '''
        model = ShaktiEntrepreneur
        fields = ('id', 'code')


class ShaktiEntrepreneurUserSerializer(serializers.ModelSerializer):
    '''
    get user details of shakti enterpreneur
    '''
    shakti_user = ShaktiEntrepreneurDetailsSerializer(
        read_only=True)

    class Meta(object):
        model = User
        fields = ('id', 'name', 'image', 'shakti_user')
