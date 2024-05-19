from django.urls import re_path
from django.contrib import admin
from rpfti.views import wai, mon, info, amoral

admin.autodiscover()

urlpatterns = [re_path(r'^wai/$', wai, name='wai'),
               re_path(r'^info/$', info, name='info'),
               re_path(r'^amoral/$', amoral, name='amoral'),
               re_path(r'^mon/$', mon, name='mon')]
