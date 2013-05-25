import django.dispatch

ebay_platform_notification = django.dispatch.Signal(providing_args=["payload"])

selling_poller_item = django.dispatch.Signal(providing_args=["item", "username"])