from django.conf.urls import url
from django.contrib import admin
from rpfti.views import wai, mon, info, amoral

admin.autodiscover()

urlpatterns = [url(r'^wai/$', wai, name='wai'),
               url(r'^info/$', info, name='info'),
               url(r'^amoral/$', amoral, name='amoral'),
               url(r'^mon/$', mon, name='mon')]
