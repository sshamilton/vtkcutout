from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^cutout/', include('cutout.urls')),
    url(r'^admin/', include(admin.site.urls)),
]

