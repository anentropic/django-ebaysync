import logging
import os
import warnings
from functools import wraps

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from ebaysuds import EbaySuds, WSDL_URL
from suds.plugin import PluginContainer

from . import NOTIFICATION_PAYLOADS
from .notifications import NotificationHandler
from .signals import ebay_platform_notification


logging.basicConfig()
log = logging.getLogger(__name__)


def get_notification_url():
    current_site = Site.objects.get_current()
    if current_site.domain == 'example.com':
        warnings.warn("You have not configured your Django sites framework, current site points to example.com")
    return 'http://%s%s' % (current_site.domain, reverse('ebaysync:notification'))


@require_POST
@csrf_exempt
def notification(request):
    try:
        action = request.META['HTTP_SOAPACTION']
    except KeyError:
        msg = 'Missing SOAPACTION header.'
        log.error(msg)
        return HttpResponseBadRequest(msg)
    else:
        action = action.strip('"')

    try:
        notification_type = action.split('/')[-1]
    except IndexError:
        msg = 'Could not parse notification type from SOAPACTION: %s' % action
        log.error(msg)
        return HttpResponseBadRequest(msg)

    try:
        payload_type = NOTIFICATION_PAYLOADS[notification_type]
    except KeyError:
        msg = 'Unrecognised notification type: %s' % notification_type
        log.error(msg)
        return HttpResponseBadRequest(msg)

    handler = NotificationHandler(WSDL_URL)
    payload = handler.decode(payload_type, request.body)

    # fire django signal
    ebay_platform_notification.send_robust(sender=notification_type, payload=payload)

    return HttpResponse('OK baby')
