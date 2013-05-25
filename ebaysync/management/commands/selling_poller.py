from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from ebaysync.models import UserToken
from ebaysync.signallers import my_ebay_selling
from ebaysync.signals import selling_poller_item


class Command(BaseCommand):
    #args = '<response_section response_section ...>'
    help = ("It's recommended to limit the included sections to only those "
            "needed. Choose from: %s" % ', '.join(INCLUDABLE_SECTIONS))

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
        user = None
        # note: keys are always present in options dict (with None value) even if not given by user
        if options['wsdl']:
            ebay_kwargs['wsdl_url'] = options.pop('wsdl')
        if options['sandbox']:
            ebay_kwargs['sandbox'] = True
            options.pop('sandbox')
        if options['for']:
            ebay_kwargs['user_token_obj'] = UserToken.objects.get(ebay_username=options.pop('for'))

        # do API call, parse response and send signals
        my_ebay_selling(sections=args, **ebay_kwargs)
