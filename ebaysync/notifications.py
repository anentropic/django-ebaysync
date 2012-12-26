import base64
import hashlib
import math
import time

from ebaysuds import EbaySuds, WSDL_URL, ebaysuds_config
from suds.plugin import PluginContainer


class UnrecognisedPayloadTypeError(Exception):
    pass

class NotificationValidationError(Exception):
    pass

class TimestampOutOfBounds(NotificationValidationError):
    pass

class InvalidSignature(NotificationValidationError):
    pass


class NotificationHandler(object):
    def __init__(self, wsdl_url=WSDL_URL, token=None, sandbox=False):
        es_kwargs = {
            'wsdl_url': wsdl_url,
            'sandbox': sandbox,
        }
        if token is not None:
            es_kwargs['token'] = token
        self.client = EbaySuds(**es_kwargs)

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

        if self.validate(result):
            return result

    def validate(self, message):
        """
        As per:
        http://developer.ebay.com/DevZone/XML/docs/WebHelp/wwhelp/wwhimpl/common/html/wwhelp.htm?context=eBay_XML_API&file=WorkingWithNotifications-Receiving_Platform_Notifications.html
        """
        
        # check timestamp is within 10 minutes of current time
        timestamp = time.mktime(message.Timestamp.timetuple())
        diff_seconds = math.fabs(time.time() - timestamp)
        if diff_seconds > 600:
            raise TimestampOutOfBounds("Payload timestamp was %s seconds away from current time." % diff_seconds)
        
        # make hash
        m = hashlib.md5()
        m.update(str(timestamp))
        m.update(ebaysuds_config.get('keys', 'dev_id'))
        if self.client.sandbox:
            conf_section = 'sandbox_keys'
        else:
            conf_section = 'production_keys'
        # sandbox?  
        m.update(ebaysuds_config.get(conf_section, 'app_id'))
        m.update(ebaysuds_config.get(conf_section, 'cert_id'))
        computed_hash = base64.standard_b64encode(m.hexdigest())
        if computed_hash != message.RequesterCredentials.NotificationSignature:
            raise InvalidSignature(message.RequesterCredentials.NotificationSignature)

        return True
