'''
for handling urls of master app
'''
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from master.api import GetAllCountries


urlpatterns = [
    url(r'^api/getcountries/$', GetAllCountries.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
