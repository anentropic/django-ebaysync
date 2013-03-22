from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from ebaysuds import TradingAPI

from ...views import get_notification_url
from ...models import UserToken


class Command(BaseCommand):
    args = '<notification_type notification_type ...>'
    help = 'Call without args to GetNotificationPreferences, with args to SetNotificationPreferences.'

    option_list = BaseCommand.option_list + (
        make_option('--for',
                    help='eBay username to set/get preferences for (must exist as UserToken record in db),\
                          will use the auth token from ebaysuds.conf if ommitted'),
        make_option('--wsdl',
                    help='URL to the eBay API WSDL (eg to use your own pruned version)'),
        make_option('--sandbox', action='store_true',
                    help='Connect to sandbox API (selected automatically if using --for with a sandbox user)'),
    )

    def handle(self, *args, **options):
        ebay_kwargs = {}
        # note: keys are always present in options dict (with None value) even if not given by user
        if options['wsdl']:
            ebay_kwargs['wsdl_url'] = options['wsdl']
        if options['sandbox']:
            ebay_kwargs['sandbox'] = True
        if options['for']:
            user = UserToken.objects.get(ebay_username=options['for'])
            ebay_kwargs['token'] = user.token
            ebay_kwargs['sandbox'] = user.is_sandbox
        client = TradingAPI(**ebay_kwargs)

        if args:
            app_prefs = client.sudsclient.factory.create('ApplicationDeliveryPreferencesType')
            app_prefs.AlertEnable = 'Enable'
            app_prefs.ApplicationURL = get_notification_url(username=options['for'])
            app_prefs.ApplicationEnable = 'Enable'
            # these fields are optional but suds sends empty keys for them if you don't give values
            app_prefs.DeviceType = 'Platform'
            app_prefs.NotificationPayloadType = 'eBLSchemaSOAP'

            user_prefs = client.sudsclient.factory.create('NotificationEnableArrayType')
            for arg in args:
                ntype = client.sudsclient.factory.create('NotificationEnableType')
                ntype.EventEnable = 'Enable'
                ntype.EventType = arg
                user_prefs.NotificationEnable.append(ntype)

            response = client.SetNotificationPreferences(
                ApplicationDeliveryPreferences=app_prefs,
                UserDeliveryPreferenceArray=user_prefs,
            )
            print response.Ack
        else:
            app_prefs = client.GetNotificationPreferences(PreferenceLevel='Application')
            print 'Application:\n%s' % app_prefs.__str__()
            user_prefs = client.GetNotificationPreferences(PreferenceLevel='User')
            print 'User:\n%s' % user_prefs.__str__()
