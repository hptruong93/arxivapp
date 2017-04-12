from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib.auth import views as auth_views
from django.contrib import admin
from arxivapp import views
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.index, name='main_index'),

	url(r'^accounts/password_change/$', auth_views.password_change, name = 'password_change'),
	url(r'^accounts/password_change_done/$', auth_views.password_change_done, name = 'password_change_done'),

    url(r'^accounts/password_reset/$', auth_views.password_reset, name = 'password_reset'),
    url(r'^accounts/password_reset_done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^accounts/password_reset_confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, name = 'password_reset_confirm'),
    url(r'^accounts/password_reset_complete/$', auth_views.password_reset_complete, name = 'password_reset_complete'),

    url('', include('social.apps.django_app.urls', namespace='social')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^main_app/', include('main_app.urls')),
)

urlpatterns += staticfiles_urlpatterns()
