import base64
import hashlib
import logging
import math
import time

from django.conf import settings
from ebaysuds import TradingAPI
from suds.plugin import PluginContainer
from suds.sax.parser import Parser


logging.basicConfig()
log = logging.getLogger(__name__)


class UnrecognisedPayloadTypeError(Exception):
    pass

class NotificationValidationError(Exception):
    pass

class TimestampOutOfBounds(NotificationValidationError):
    pass

class InvalidSignature(NotificationValidationError):
    pass


def ebay_timestamp_string(datetime_obj):
    # convert python datetime obj to string representation used by eBay
    # appears to be a bug in suds - eBay's milliseconds are loaded into python datetime
    # as microseconds so the datetime_obj we get from suds is not accurate to the data
    return '%(year)s-%(month)s-%(day)sT%(hour)s:%(minute)s:%(second)s.%(millisecond)sZ' % {
        'year': '%04d' % datetime_obj.year,
        'month': '%02d' % datetime_obj.month,
        'day': '%02d' % datetime_obj.day,
        'hour': '%02d' % datetime_obj.hour,
        'minute': '%02d' % datetime_obj.minute,
        'second': '%02d' % datetime_obj.second,
        'millisecond': '%03d' % datetime_obj.microsecond# don't need to x1000 as we're omitting three digits of zero-padding
    }


class NotificationHandler(object):
    def __init__(self, wsdl_url=None, token=None, sandbox=False, _validate=True):
        es_kwargs = {
            'sandbox': sandbox,
        }
        if wsdl_url is not None:
            es_kwargs['wsdl_url'] = wsdl_url
        if token is not None:
            es_kwargs['token'] = token
        self.client = TradingAPI(**es_kwargs)
        self.saxparser = Parser()
        self._validate = _validate

    def decode(self, payload_type, message):
        try:
            payload_method = getattr(self.client.sudsclient.service, payload_type)
        except AttributeError:
            raise UnrecognisedPayloadTypeError('Unrecognised payload type: %s' % payload_type)

        # don balaclava, hijack a suds SoapClient instance to decode our payload for us
        sc_class = payload_method.clientclass({})
        soapclient = sc_class(self.client.sudsclient, payload_method.method)
        
        # copy+pasted from SoapClient.send :(
        plugins = PluginContainer(soapclient.options.plugins)
        ctx = plugins.message.received(reply=message)
        result = soapclient.succeeded(soapclient.method.binding.input, ctx.reply)

        # `result` only contains the soap:Body of the response (parsed into objects)
        # but the signature we need is in the soap:Header element
        signature = self._parse_signature(message)

        if not self._validate or self.validate(result, signature):
            return result

    def _parse_signature(self, message):
        xml = self.saxparser.parse(string=message)
        return xml.getChild("Envelope").getChild("Header").getChild('RequesterCredentials').getChild('NotificationSignature').text

    def validate(self, message, signature):
        """
        As per:
        http://developer.ebay.com/DevZone/XML/docs/WebHelp/wwhelp/wwhimpl/common/html/wwhelp.htm?context=eBay_XML_API&file=WorkingWithNotifications-Receiving_Platform_Notifications.html
        """
        
        timestamp_str = ebay_timestamp_string(message.Timestamp)
        floattime = time.mktime(message.Timestamp.timetuple())
        if not settings.DEBUG:
            # check timestamp is within 10 minutes of current time
            diff_seconds = math.fabs(time.time() - floattime)
            if diff_seconds > 600:
                raise TimestampOutOfBounds("Payload timestamp was %s seconds away from current time." % diff_seconds)
        
        # make hash
        m = hashlib.md5()
        m.update(timestamp_str)
        m.update(self.client.config.get('keys', 'dev_id'))
        m.update(self.client.config.get('keys', 'app_id'))
        m.update(self.client.config.get('keys', 'cert_id'))
        computed_hash = base64.standard_b64encode(m.digest())
        if computed_hash != signature:
            raise InvalidSignature("%s != %s" % (computed_hash, signature))

        return True
