'''app/urls.py'''
from django.conf.urls import url
from app.api import (Login, SignOut, Profile, ChangePassword, SetForgotPassword,
                     ValidateOTP, ResetPasswordView, GetShaktiEntrepreneur,
                     GetAlliancePartner, SEProfile)
from app import ajax
from.views import TaskStatus, download_file_view

urlpatterns = [
    url(r'^login/$', Login.as_view()),
    url(r'^signout/$', SignOut.as_view()),
    url(r'^(?i)profile/$', Profile.as_view()),
    url(r'^(?i)seprofile/$', SEProfile.as_view()),
    url(r'^(?i)changepassword/$', ChangePassword.as_view()),
    url(r'^(?i)forgotpassword/$', SetForgotPassword.as_view()),
    url(r'^(?i)validateotp/$', ValidateOTP.as_view()),
    url(r'^(?i)resetpassword/$', ResetPasswordView.as_view()),
    url(r'^(?i)shaktientrepreneurs/(?P<page>[0-9]+)/$',
        GetShaktiEntrepreneur.as_view()),
    url(r'^(?i)alliancepartners/(?P<page>[0-9]+)/$',
        GetAlliancePartner.as_view()),
]

urlpatterns += [
    url(r'^app/get_partner_code/$', ajax.get_partner_code, name="get_partner_code"),
    url(r'^async/task-status/$', TaskStatus.as_view(), name='task_status'),
    url(r'^download/export/$', download_file_view, name="download-export"),
]

