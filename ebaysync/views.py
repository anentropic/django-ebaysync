import copy
import logging
import os
import pickle
import warnings
from functools import wraps

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from ebaysuds import EbaySuds
from suds.plugin import PluginContainer

from . import NOTIFICATION_PAYLOADS
from .models import UserToken
from .notifications import NotificationHandler
from .signals import ebay_platform_notification


logging.basicConfig()
log = logging.getLogger(__name__)


def get_notification_url(username=None):
    current_site = Site.objects.get_current()
    if current_site.domain == 'example.com':
        warnings.warn("You have not configured your Django sites framework, current site points to example.com")
    return 'http://%s%s' % (current_site.domain, reverse('ebaysync:notification', kwargs={'username': username}))


@require_POST
@csrf_exempt
def notification(request, username=None):
    if settings.DEBUG:
        with open(os.path.join(settings.PROJECT_ROOT, 'last_request.pkl'), 'wb') as output:
            meta = dict([(k,v) for k,v in request.META.items() if isinstance(v, basestring)])
            obj = {'META': meta, 'body': request.body}
            pickle.dump(obj, output)
    
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

    nh_kwargs = {}
    if username is not None:
        user = get_object_or_404(UserToken, ebay_username=username)
        nh_kwargs['token'] = user.token
        nh_kwargs['sandbox'] = user.is_sandbox
    handler = NotificationHandler(**nh_kwargs)
    payload = handler.decode(payload_type, request.body)
    log.info(payload)

    # fire django signal
    ebay_platform_notification.send_robust(sender=notification_type, payload=payload)

    return HttpResponse('OK baby')
