import logging
from collections import namedtuple
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from ebaysuds import TradingAPI
from ebaysync.signals import ebay_platform_notification, selling_poller_item
from ebaysync.models import UserToken


logging.basicConfig()
log = logging.getLogger(__name__)

OMIT_ATTRS = ('RelistParentID',)

INCLUDABLE_SECTIONS = set([
    'ActiveList', 'BidList', 'DeletedFromSoldList', 'DeletedFromUnsoldList',
    'ScheduledList', 'SellingSummary', 'SoldList', 'UnsoldList',
])
SELLING_ITEM_TYPES = {}
for stype in INCLUDABLE_SECTIONS:
    SELLING_ITEM_TYPES[stype] = namedtuple(stype, [])

# not sure whether it's a quirk of Suds or of eBay, but some sections return a
# response with a differently-named element so we have to translate
RESPONSE_SECTIONS = {
    'SellingSummary': 'Summary',
}


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
            user = UserToken.objects.get(ebay_username=options.pop('for'))
            ebay_kwargs['token'] = user.token
            ebay_kwargs['sandbox'] = user.is_sandbox
        client = TradingAPI(**ebay_kwargs)

        if user is None:
            token = client.config.get('auth', 'token')
            user = UserToken.objects.get(token=token)

        # by using ReturnAll detail level we have to specifically exclude unwanted sections
        include_sections = INCLUDABLE_SECTIONS & set(options)
        exclude_sections = INCLUDABLE_SECTIONS - include_sections
        call_kwargs = {
            'DetailLevel': 'ReturnAll',
            'MessageID': user.ebay_username,  # returned as CorrelationID in the response
        }
        for section in exclude_sections:
            call_kwargs[section] = {'Include': False}

        response = client.GetMyeBaySelling(**call_kwargs)

        if response and response.Ack.lower() in ("success","warning"):
            for section in include_sections:
                response_section = getattr(response, RESPONSE_SECTIONS.get(section, section))
                if not hasattr(response_section, 'ItemArray'):
                    continue
                for item in response_section.ItemArray.Item:
                    selling_poller_item.send_robust(sender=SELLING_ITEM_TYPES[section], item=item)
