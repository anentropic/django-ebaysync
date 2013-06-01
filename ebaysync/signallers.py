import logging
from collections import namedtuple

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


def my_ebay_selling(user_token_obj=None, sections=None, sandbox=False, wsdl_url=None):
    """
    Makes a GetMyeBaySelling request and for each item in the specified sections
    (eg ['UnsoldList']) sends a `selling_poller_item` signal with the item attached
    """
    ebay_kwargs = {}
    if wsdl_url is not None:
        ebay_kwargs['wsdl_url'] = wsdl_url
    ebay_kwargs['sandbox'] = sandbox
    if user_token_obj is not None:
        ebay_kwargs['token'] = user_token_obj.token
        ebay_kwargs['sandbox'] = user_token_obj.is_sandbox
    client = TradingAPI(**ebay_kwargs)

    # if no UserToken instance supplied, get default user and token from ebaysuds.conf
    if user_token_obj is None:
        token = client.config.get('auth', 'token')
        user = UserToken.objects.get(token=token)

    if sections is None:
        sections = []

    # by using ReturnAll detail level we have to specifically exclude unwanted sections
    include_sections = INCLUDABLE_SECTIONS & set(sections)
    exclude_sections = INCLUDABLE_SECTIONS - include_sections
    call_kwargs = {
        'DetailLevel': 'ReturnAll',
        'MessageID': user_token_obj.ebay_username,  # returned as CorrelationID in the response
    }
    for section in exclude_sections:
        call_kwargs[section] = {'Include': False}

    response = client.GetMyeBaySelling(**call_kwargs)

    if not response:
        log.error("No response from GetMyeBaySelling call")
        return

    if response.Ack.lower() != 'success':
        log.info(response.Ack)
        log.info(response.Errors)

    if response.Ack.lower() in ("success","warning"):
        for section in include_sections:
            response_section = getattr(response, RESPONSE_SECTIONS.get(section, section))
            if not hasattr(response_section, 'ItemArray'):
                continue
            for item in response_section.ItemArray.Item:
                selling_poller_item.send_robust(
                    sender=SELLING_ITEM_TYPES[section],
                    item=item,
                    username=user.ebay_username
                )
