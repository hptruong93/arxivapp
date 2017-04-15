
from django.conf.urls import patterns, url

from main_app import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^login$', views.login, name='arxiv_login'),
    url(r'^login/(.*)$', views.login, name='login_link'),
    url(r'^logout$', views.logout, name='arxiv_logout'),
    url(r'^signup$', views.signup, name='signup'),

    url(r'^browse$', views.browse, name='browse'),
    url(r'^history$', views.history, name='history'),
    url(r'^bookmark$', views.bookmark, name='bookmark'), # The action
    url(r'^bookmarks$', views.bookmarks, name='bookmarks'), # The page
    url(r'^author/([0-9]+)$', views.author, name='author'),
    url(r'^category/(.*?)$', views.category, name='category'),

    url(r'^paper/(?P<paper_id>.+)$', views.paper, name='paper'),
    url(r'^abstract/(.+?)$', views.arxiv_abstract, name='abstract'), # Abstract on arxiv.org
    url(r'^pdf/(.+?)$', views.pdf, name='pdf'),
    url(r'^search', views.search, name='search'),
)
