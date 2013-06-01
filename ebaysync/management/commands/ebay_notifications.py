from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from ebaysuds import TradingAPI

from ...views import get_notification_url
from ...models import UserToken


# if these keys are in options we want to set prefs, not get them
SET_PREFS_KEYS = (
    'disable_markdown_alerts',
    'disable_application',
    'enable_markdown_alerts',
    'enable_application',
)


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
        make_option('--disable', action='store_true',
                    help='Disable the specified notification types rather than enabling them'),
        make_option('--disable-application', action='store_true',
                    help='Disable all notifications for the app (while preserving individual notification preferences)'),
        make_option('--disable-markdown-alerts', action='store_true',
                    help="Disable the sending of alerts when eBay disables notifications (e.g. due to\
                          undeliverability) for your app. You probably don't want this."),
        make_option('--enable-application', action='store_true',
                    help='Set to enable notifications for the app (while preserving individual notification preferences)'),
        make_option('--enable-markdown-alerts', action='store_true',
                    help="Set enabled the sending of alerts when eBay disables notifications (e.g. due to\
                          undeliverability) for your app."),
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

        alert_enable = True
        if options['disable_markdown_alerts']:
            alert_enable = False
        if options['enable_markdown_alerts']:
            alert_enable = True

        notifications_enable = True
        if options['disable_application']:
            notifications_enable = False
        if options['enable_application']:
            notifications_enable = True

        if args or any((True for (k,v) in options.items() if k in SET_PREFS_KEYS and v is not None)):
            print "SET"
            app_prefs = client.sudsclient.factory.create('ApplicationDeliveryPreferencesType')
            app_prefs.AlertEnable = 'Enable' if alert_enable else 'Disable'
            app_prefs.ApplicationURL = get_notification_url(username=options['for'])
            app_prefs.ApplicationEnable = 'Enable' if notifications_enable else 'Disable'
            # these fields are optional in the API but suds sends empty keys
            # for them if we don't give values here
            app_prefs.DeviceType = 'Platform'
            app_prefs.NotificationPayloadType = 'eBLSchemaSOAP'

            user_prefs = client.sudsclient.factory.create('NotificationEnableArrayType')
            for arg in args:
                ntype = client.sudsclient.factory.create('NotificationEnableType')
                ntype.EventEnable = 'Disable' if options['disable'] else 'Enable'
                ntype.EventType = arg
                user_prefs.NotificationEnable.append(ntype)

            response = client.SetNotificationPreferences(
                ApplicationDeliveryPreferences=app_prefs,
                UserDeliveryPreferenceArray=user_prefs,
            )
            print response.Ack
        else:
            print "GET"
            app_prefs = client.GetNotificationPreferences(PreferenceLevel='Application')
            print 'Application:\n%s' % app_prefs.__str__()
            user_prefs = client.GetNotificationPreferences(PreferenceLevel='User')
            print 'User:\n%s' % user_prefs.__str__()
