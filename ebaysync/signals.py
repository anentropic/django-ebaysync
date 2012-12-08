import django.dispatch

ebay_platform_notification = django.dispatch.Signal(providing_args=["payload"])