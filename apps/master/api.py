'''
for handling all the master app requests
'''
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from .models import Country
from .serializers import CountriesSerializer
from hul.utility import HulUtility


# Create your views here.
class GetAllCountries(generics.ListAPIView):
    '''
    API for getting the listof countries.
    '''
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountriesSerializer

    def get(self, request, *args, **kwargs):
        'for handling get request for countries'
        countries = self.list(request, *args, **kwargs)
        response_data = {}
        response_data['countries'] = countries.data
        response = HulUtility.data_wrapper(response_data)
        return Response(response, status=status.HTTP_200_OK)
