import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from ebaysuds import TradingAPI
from ebaysync.models import UserToken
from ebaysync.myebay import selling_items, INCLUDABLE_SECTIONS
from ebaysync.signals import selling_poller_item


logging.basicConfig()
log = logging.getLogger(__name__)


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
        # note: keys are always present in options dict (with None value) even if not given by user
        if options['wsdl']:
            ebay_kwargs['wsdl_url'] = options.pop('wsdl')
        if options['sandbox']:
            ebay_kwargs['sandbox'] = True
            options.pop('sandbox')
        if options['for']:
            # Note: iexact doesn't work properly in SQLite, type it correctly!
            ut = UserToken.objects.get(ebay_username__iexact=options.pop('for'))
            ebay_kwargs['token'] = ut.token
            ebay_kwargs['sandbox'] = ut.is_sandbox

        client = TradingAPI(**ebay_kwargs)

        # do API call, parse response and send signals
        for section_cls, item, total in selling_items(sections=args, client=client):
            log.info('selling_poller: %s > %s', section_cls.__name__, item.ItemID)
            selling_poller_item.send_robust(
                sender=section_cls,
                item=item,
                client=client,
            )