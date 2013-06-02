from django.db import models


class UserToken(models.Model):
    ebay_username = models.CharField(max_length=255, primary_key=True)
    token = models.TextField(unique=True)

    @property
    def is_sandbox(self):
        # sandbox user name is created as 'TESTUSER_x' but elsewhere eBay
        # usernames seem to be case-insensitive so I don't trust them to
        # always send back the original uppercase prefix...
        return self.ebay_username.lower().startswith('testuser_')

    def __unicode__(self):
        return self.ebay_username