import os
import warnings
from functools import wraps

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from ebaysuds import EbaySuds, WSDL_URL
from suds.plugin import PluginContainer

from . import NOTIFICATION_PAYLOADS
from .signals import ebay_platform_notification


def get_notification_url():
    current_site = Site.objects.get_current()
    if current_site.domain == 'example.com':
        warnings.warn("You have not configured your Django sites framework, current site points to example.com")
    return 'http://%s%s' % (current_site.domain, reverse('ebaysync:notification'))


@require_POST
def notification(request):
    try:
        action = request.META['HTTP_SOAPACTION']
    except KeyError:
        return HttpResponseBadRequest('Missing SOAPACTION header.')

    try:
        notification_type = action.split('/')[-1]
    except IndexError:
        return HttpResponseBadRequest('Could not parse notification type from SOAPACTION: %s' % action)

    try:
        payload_type = NOTIFICATION_PAYLOADS[notification_type]
    except KeyError:
        return HttpResponseBadRequest('Unrecognised notification type: %s' % notification_type)

    handler = NotificationHandler(WSDL_URL)
    payload = handler.decode(payload_type, request.body)

    # fire django signal
    ebay_platform_notification.send_robust(sender=notification_type, payload=payload)

    return HttpResponse('OK baby')
