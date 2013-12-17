import logging

from ebaysync.management.base import BaseEbayCommand
from ebaysync.myebay import selling_items, INCLUDABLE_SECTIONS
from ebaysync.signals import selling_poller_item

logging.basicConfig()
log = logging.getLogger(__name__)


class Command(BaseEbayCommand):
    #args = '<response_section response_section ...>'
    help = ("It's recommended to limit the included sections to only those "
            "needed. Choose from: %s" % ', '.join(INCLUDABLE_SECTIONS))

    def handle(self, *args, **options):
        client = self.get_ebay_client(options)

        # do API call, parse response and send signals
        for section_cls, item, total in selling_items(sections=args, client=client):
            log.info('selling_poller: %s > %s', section_cls.__name__, item.ItemID)
            selling_poller_item.send_robust(
                sender=section_cls,
                item=item,
                client=client,
            )
