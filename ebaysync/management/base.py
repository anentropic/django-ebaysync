import inspect
import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from ebaysuds import TradingAPI
from ebaysync.models import UserToken


logging.basicConfig()
log = logging.getLogger(__name__)


class BaseEbayCommand(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--for',
                    help='eBay seller username to connect as (must exist as '
                         'UserToken record in db), will use the auth token '
                         'from ebaysuds.conf if ommitted'),
        make_option('--wsdl',
                    help='URL to the eBay API WSDL (eg to use your own pruned '
                         'version)'),
        make_option('--sandbox', action='store_true',
                    help='Connect to sandbox API (selected automatically if '
                         'using --for with a sandbox user)'),
    )

    def __init__(self):
        super(BaseEbayCommand, self).__init__()
        self.name = inspect.getmodule(self).__name__.split('.')[-1]

    def get_ebay_client(self, options):
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

        return TradingAPI(**ebay_kwargs)
