from django.contrib.auth import models as auth_models
from django.db import models

class AbstractUserHistory(models.Model):
    class Meta:
        abstract = True

    user = models.ForeignKey(auth_models.User)
    last_access = models.DateTimeField(auto_now_add=True)
    count = models.IntegerField(default = 0)

    def __unicode__(self):
        return unicode(self.user) + ' with count = '  + unicode(self.count)