from django.conf.urls import url
from django.contrib import admin
from rpfti.views import bot, mon

admin.autodiscover()


urlpatterns = [url(r'^bot/$', bot, name='bot'),
               url(r'^mon/$', mon, name='mon')]
