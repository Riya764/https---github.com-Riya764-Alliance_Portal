'''product urls.py'''
from django.conf.urls import url
from product.api import Products, ProductCategory

urlpatterns = [
    url(r'^products/$', Products.as_view()),
    url(r'^categories/$', ProductCategory.as_view())
]
