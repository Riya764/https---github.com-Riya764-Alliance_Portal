'''cms urls.py'''
from django.conf.urls import url
from cms import views

urlpatterns = [
    url(r'^(?i)aboutus/$', views.aboutus, name='aboutus'),
]
