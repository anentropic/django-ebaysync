from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from ebaysuds import EbaySuds

from ...views import get_notification_url
from ...models import UserToken


class Command(BaseCommand):
    args = '<notification_type notification_type ...>'
    help = 'Call without args to GetNotificationPreferences, with args to SetNotificationPreferences.'

    option_list = BaseCommand.option_list + (
        make_option('--for',
                    help='eBay username to set/get preferences for (must exist as UserToken record in db), will use the one from ebaysuds.conf if ommitted'),
        make_option('--wsdl',
                    help='URL to the eBay API WSDL (eg to use your own pruned version)'),
    )

    def handle(self, *args, **options):
        es_kwargs = {}
        if 'wsdl' in options:
            es_kwargs['wsdl_url'] = options['wsdl']
        if 'for' in options:
            user = UserToken.objects.get(ebay_username=options['for'])
            es_kwargs['token'] = user.token
        client = EbaySuds(**es_kwargs)

        if args:
            app_prefs = client.sudsclient.factory.create('ApplicationDeliveryPreferencesType')
            app_prefs.AlertEnable = 'Enable'
            app_prefs.ApplicationURL = get_notification_url()
            app_prefs.ApplicationEnable = 'Enable'

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