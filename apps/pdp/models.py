from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

from app.models import ShaktiEntrepreneur, RegionalDistributor


class TodayShakti(ShaktiEntrepreneur):

    class Meta(object):
        proxy = True
        verbose_name = _('Today\'s PDP Shakti Entrepreneur')
        verbose_name_plural = _('Today\'s PDP Shakti Entrepreneurs')

    def __str__(self):
        return self.user.name


class TodayRS(RegionalDistributor):

    class Meta(object):
        proxy = True
        verbose_name = _('Today\'s PDP RS')
        verbose_name_plural = _('Today\'s PDP RS')
