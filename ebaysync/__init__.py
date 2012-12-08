# generated from the table at:
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
 'Feedback Notifications': 'GetFeedback',
 'FeedbackLeft': 'GetFeedback',
 'FeedbackReceived': 'GetFeedback',
 'FeedbackStarChanged': 'GetUser',
 'FixedPriceEndOfTransaction': 'GetItemTransactions',
 'FixedPriceTransaction': 'GetItemTransactions',

 # expanded from "INR (ItemNotReceived) Notifications" in the table:
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
 'MyMessages Notification': 'GetMyMessages',
 'OutBid': 'GetItem',
 'SecondChanceOffer': 'GetItem',
 'TokenRevocation': 'GetNotificationPreferences',
}