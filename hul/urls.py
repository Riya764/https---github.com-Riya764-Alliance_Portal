'''root url.py'''
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import logout
# from django.contrib.auth.views import (login as admin_login, logout as admin_logout,
#                                        password_reset as admin_password_reset,
#                                        password_reset_done as admin_password_reset_done,
#                                        password_reset_complete as admin_password_reset_complete,
#                                        password_reset_confirm as admin_password_reset_confirm)
# from apps.app.password import (password_reset, password_reset_complete,
#                                password_reset_confirm, password_reset_done)
from apps.app.views import view_site

urlpatterns = [
    # url(r'^(?i)user/password_reset/$', password_reset, name='password_reset'),
    # url(r'^(?i)user/password_reset/done/$', password_reset_done,
    #     name='password_reset_done'),
    # url(r'^(?i)user/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
    #     password_reset_confirm, name='password_reset_confirm'),
    # url(r'^(?i)user/reset/done/$', password_reset_complete,
    #     name='password_reset_complete'),

    # url(r'^(?i)admin/login/', admin_login,
    #     {'template_name': 'admin/custom_login.html'}),
    # url(r'^(?i)admin/logout/$', admin_logout,
    #     {'next_page': '/admin/login/?next=/admin/'}),
    # url(r'^(?i)accounts/login/$', admin_logout, {'next_page': '/admin/login/?next=/admin/',
    #                                              'template_name': 'custom_login.html'}),
    # url(r'^(?i)admin/password_reset/$',
    #     admin_password_reset, {'post_reset_redirect': 'done/'}, name='admin_password_reset'),
    # url(r'^admin/password_reset/done/$', admin_password_reset_done,
    #     name='admin_password_reset_done'),
    # url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
    #     admin_password_reset_confirm, name='admin_password_reset_confirm'),
    # url(r'^reset/done/$', admin_password_reset_complete,
    #     name='admin_password_reset_complete'),
    url(r'^admin/logout/$', logout,
        {'next_page': '/admin/login'}),
    url(r'^admin/password_reset/$', auth_views.password_reset,
        name='admin_password_reset'),
    url(r'^admin/password_reset/done/$',
        auth_views.password_reset_done, name='password_reset_done'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', auth_views.password_reset_complete,
        name='password_reset_complete'),
    url(r'^cms/', include('cms.urls')),
    url(r'^', include('app.urls')),
    url(r'^', include('product.urls')),
    url(r'^', include('orders.urls')),
    url(r'^', include('misreporting.urls', namespace='misreporting')),
    url(r'^$', view_site),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^s3direct/', include('s3direct.urls')),
    # url(r'^static/(?P<path>.*)$', 'django.views.static.serve',{'document_root', settings.STATIC_URL}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
