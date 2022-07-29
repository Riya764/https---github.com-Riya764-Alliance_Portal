'''order/urls.py'''
from django.conf.urls import url
from .views import DistributorByBrand, RspByDistributor, ShaktiByRsp, RspByAlliance, ShaktiByAlliance

urlpatterns = [
   url(r'^distributor-by-brand/$', DistributorByBrand.as_view(), name="distributor-by-brand"),
   url(r'^rsp-by-distributor/$', RspByDistributor.as_view(), name="rsp-by-distributor"),
   url(r'^shakti-by-rsp/$', ShaktiByRsp.as_view(), name="shakti-by-rsp"),
   url(r'^rsp-by-alliance/$', RspByAlliance.as_view(), name="rsp-by-alliance"),
   url(r'^shakti-by-alliance/$', ShaktiByAlliance.as_view(), name="shakti-by-alliance"),

   
]
