
from django.conf.urls import patterns, url

from main_app import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^login$', views.login, name='login'),
    url(r'^login/(.*)$', views.login, name='login_link'),
    url(r'^signup$', views.signup, name='signup'),
    url(r'^history$', views.history, name='history'),
    url(r'^author/([0-9]+)$', views.author, name='author'),
    url(r'^category/(.*?)$', views.category, name='category'),
    url(r'^paper/(.+?)$', views.paper, name='paper'),
    url(r'^pdf/(.+?)$', views.pdf, name='pdf'),
    url(r'^search', views.search, name='search'),
)
