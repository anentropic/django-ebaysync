from collections import namedtuple

# beware of circular imports
from .signallers import SELLING_ITEM_TYPES


# partly generated from the table at:
# http://developer.ebay.com/DevZone/XML/docs/WebHelp/wwhelp/wwhimpl/common/html/wwhelp.htm?context=eBay_XML_API&file=WorkingWithNotifications-Receiving_Platform_Notifications.html

NOTIFICATION_PAYLOADS = {
 'AskSellerQuestion': 'GetMemberMessages',
 'AuctionCheckoutComplete': 'GetItemTransactions',
 'BestOffer': 'GetBestOffers',
 'BestOfferDeclined': 'GetBestOffers',
 'BestOfferPlaced': 'GetBestOffers',
 'BidPlaced': 'GetItem',
 'BidReceived': 'GetItem',
 'CheckoutBuyerRequestsTotal': 'GetItemTransactions',
 'CounterOfferReceived': 'GetBestOffers',
 'EndOfAuction': 'GetItemTransactions',
 'Feedback': 'GetFeedback',
 'FeedbackLeft': 'GetFeedback',
 'FeedbackReceived': 'GetFeedback',
 'FeedbackStarChanged': 'GetUser',
 'FixedPriceEndOfTransaction': 'GetItemTransactions',
 'FixedPriceTransaction': 'GetItemTransactions',
 'INRBuyerOpenedDispute': 'GetDispute',
 'INRBuyerRespondedToDispute': 'GetDispute',
 'INRBuyerClosedDispute': 'GetDispute',
 'INRSellerRespondedToDispute': 'GetDispute',
 'ItemAddedToBidGroup': 'GetItem',
 'ItemAddedToWatchList': 'GetItem',
 'ItemLost': 'GetItem',
 'ItemRemovedFromBidGroup': 'GetItem',
 'ItemRemovedFromWatchList': 'GetItem',
 'ItemRevised': 'GetItem',
 'ItemRevisedAddCharity': 'GetItem',
 'ItemSold': 'GetItem',
 'ItemUnsold': 'GetItem',
 'ItemWon': 'GetItem',
 'MyMessages': 'GetMyMessages',
 'MyMessagesAlert': 'GetMyMessages',
 'MyMessagesAlertHeader': 'GetMyMessages',
 'MyMessageseBayMessage': 'GetMyMessages',
 'MyMessageseBayMessageHeader': 'GetMyMessages',
 'MyMessagesM2MMessage': 'GetMyMessages',
 'MyMessagesM2MMessageHeader': 'GetMyMessages',
 'OutBid': 'GetItem',
 'SecondChanceOffer': 'GetItem',
 'TokenRevocation': 'GetNotificationPreferences',

 # were missing from the table, added manually:
 'ItemClosed': 'GetItem',
 'ItemListed': 'GetItem',
}

# empty structs to use as distinct signal senders
NOTIFICATION_TYPES = {}
for ntype in NOTIFICATION_PAYLOADS.keys():
    NOTIFICATION_TYPES[ntype] = namedtuple(ntype, [])

