from django.db import models


class UserToken(models.Model):
    ebay_username = models.CharField(max_length=255, primary_key=True)
    token = models.TextField()

    @property
    def is_sandbox(self):
        return self.ebay_username.startswith('TESTUSER_')

    def __unicode__(self):
        return self.ebay_username