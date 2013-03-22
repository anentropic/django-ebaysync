import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from ebaysuds import TradingAPI
from ebaysync import NOTIFICATION_TYPES
from ebaysync.signals import ebay_platform_notification
from ebaysync.models import UserToken


logging.basicConfig()
log = logging.getLogger(__name__)

OMIT_ATTRS = ('RelistParentID',)

INCLUDABLE_SECTIONS = set(
    'ActiveList', 'BidList', 'DeletedFromSoldList', 'DeletedFromUnsoldList',
    'ScheduledList', 'SellingSummary', 'SoldList', 'UnsoldList',
)

# SellingStatus.HighBidder or SellingStatus.QuantitySold indicate ended due to sale

# GetItem with a TransactionID?

# if notifications are unreliable we may need to poll by crontab

# 1. poll:
#    response = client.GetMyeBaySelling(UnsoldList={'Include':True})
# 2. relist each of:
#    response.UnsoldList.ItemArray.Item[...]

# note 5000 API call per day limit
# (1440 minutes in a day... 5 minute polling should be fine) 


class Command(BaseCommand):
    #args = '<response_section response_section ...>'
    help = ("It's recommended to limit the included sections to only those "\
            "needed. Choose from: %s" % ', '.join(INCLUDABLE_SECTIONS)

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

        # by using ReturnAll detail level we have to specifically exclude unwanted sections
        include_sections = set(['UnsoldList'])
        exclude_sections = INCLUDABLE_SECTIONS - include_sections
        for section in exclude_sections:
            ebay_kwargs[section] = {'Include': False}

        response = client.GetMyeBaySelling(DetailLevel='ReturnAll')
        if response and response.Ack.lower() in ("success","warning"):
            for item in response.UnsoldList.ItemArray.Item:
                

