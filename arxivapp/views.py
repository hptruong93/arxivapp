from django import http
from django.core import urlresolvers
# Create your views here.

def index(request):
    return http.HttpResponseRedirect(urlresolvers.reverse('index'))