from optparse import make_option

from ebaysync.management.base import BaseEbayCommand
from ebaysync.views import get_notification_url


# if these keys are in options we want to set prefs, not get them
SET_PREFS_KEYS = (
    'disable_markdown_alerts',
    'disable_application',
    'enable_markdown_alerts',
    'enable_application',
)


class Command(BaseEbayCommand):
    args = '<notification_type notification_type ...>'
    help = 'Call without args to GetNotificationPreferences, with args to SetNotificationPreferences.'

    option_list = BaseEbayCommand.option_list + (
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
        client = self.get_ebay_client(options)

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
