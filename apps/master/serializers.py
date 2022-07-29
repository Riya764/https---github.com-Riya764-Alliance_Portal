'''
serializers for master app
'''
from rest_framework import serializers

from master.models import Country


class CountriesSerializer(serializers.ModelSerializer):
    '''
    for serializing country
    '''
    class Meta:
        '''
        meta for serializer of country
        '''
        model = Country
        fields = ('id', 'name', 'phone_code', 'country_code')
