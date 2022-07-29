''' Serializers.py '''
from rest_framework import serializers
from localization.models import Country, State, City, MeasurementUnit


class CountrySerializer(serializers.ModelSerializer):
    '''
    for serializing country
    '''
    class Meta(object):
        '''
        meta for serializer of country
        '''
        model = Country
        fields = ('id', 'name', 'phone_code', 'country_code')


class StateSerializer(serializers.ModelSerializer):
    '''
    for serializing country
    '''
    class Meta(object):
        '''
        meta for serializer of country
        '''
        model = State
        fields = ('id', 'name',)


class CitySerializer(serializers.ModelSerializer):
    '''
    for serializing country
    '''
    class Meta(object):
        '''
        meta for serializer of country
        '''
        model = City
        fields = ('id', 'name', )


class MeasurementUnitSerializer(serializers.ModelSerializer):
    '''
    for serializing MeasurementUnit
    '''
    class Meta(object):
        '''
        meta for serializer of MeasurementUnit
        '''
        model = MeasurementUnit
        fields = ('unit',)
