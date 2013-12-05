import logging
from collections import namedtuple

from .utils import update


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


def make_call_kwargs(include_sections, message_id=None, **kwargs):
    # by using ReturnAll detail level we have to specifically exclude unwanted sections
    exclude_sections = INCLUDABLE_SECTIONS - include_sections
    call_kwargs = {
        'DetailLevel': 'ReturnAll',
    }
    for section in exclude_sections:
        call_kwargs[section] = {'Include': False}
    for section in include_sections:
        call_kwargs[section] = {
            'Sort': 'StartTimeDescending',
            'Pagination': {
                'PageNumber': 1,
            }
        }
    if message_id is not None:
        # (returned as CorrelationID in the response)
        call_kwargs['MessageID'] = message_id

    return update(call_kwargs, kwargs)


def selling_items(client, sections=None, message_id=None, **kwargs):
    """
    Generator:
    Makes a GetMyeBaySelling request and for each item in the specified sections
    (eg ['UnsoldList']) sends a tuple which includes the item
    """
    if sections is None:
        sections = []

    include_sections = INCLUDABLE_SECTIONS & set(sections)
    call_kwargs = make_call_kwargs(include_sections, message_id, **kwargs)

    while True:
        response = client.GetMyeBaySelling(**call_kwargs)

        if not response:
            log.error("No response from GetMyeBaySelling call")
            return

        if response.Ack.lower() != 'success':
            log.info(response.Ack)
            log.info(response.Errors)

        if response.Ack.lower() in ("success", "warning"):
            for section in include_sections:
                response_section = getattr(response, RESPONSE_SECTIONS.get(section, section), None)
                if not hasattr(response_section, 'ItemArray'):
                    continue
                for item in response_section.ItemArray.Item:
                    yield (
                        SELLING_ITEM_TYPES[section],
                        item,
                    )
                log.info(response_section.PaginationResult)
                log.info(call_kwargs[section]['Pagination'])
                if call_kwargs[section]['Pagination']['PageNumber'] >= response_section.PaginationResult.TotalNumberOfPages:
                    # if we finished paging this section, don't request it next time round the loop
                    call_kwargs[section] = {'Include': False}
                else:
                    call_kwargs[section]['Pagination']['PageNumber'] += 1
        else:
            # fatal
            break

        for section in include_sections:
            if 'Include' not in call_kwargs[section] or call_kwargs[section]['Include']:
                break
        else:
            # we didn't break above, ergo no more sections need paging through
            break
