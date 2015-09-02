from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /jhtdb/
    url(r'^$', views.index, name='index'),
    #url(r'^geturl/$', views.geturl, name='geturl'),
    url(r'^getcutout/(?P<webargs>.*)$', views.getcutout, name='getcutout'),
]
