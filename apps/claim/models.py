from __future__ import unicode_literals

from django.db import models
from orders.models import AlliancePartnerOrder, AlliancePartnerDiscountDetail


class ClaimManager(models.Manager):
    def get_queryset(self):
        queryset = super(ClaimManager, self).get_queryset().filter(
            has_claim=True)
        return queryset


class Claim(AlliancePartnerOrder):
    objects = ClaimManager()

    class Meta(object):
        proxy = True
