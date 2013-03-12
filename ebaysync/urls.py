from django.conf.urls import patterns, include, url

from .views import notification


urlpatterns = patterns('',
    # url(r'^$', 'dpm.views.home', name='home'),
    url(r'^notification/(?P<username>[-_\.\*\w]+)?', notification, name="notification"),
)