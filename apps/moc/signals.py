from django.db.models.signals import post_save
from django.dispatch import receiver

from moc.models import MoCMonth, MoCYear
from moc.lib.create_moc import CreateMoC


@receiver(post_save, sender=MoCYear, dispatch_uid="generate_moc_months")
def generate_moc_months(sender, instance, **kwargs):

    if kwargs.get('created'):
        CreateMoC.create_moc_month(instance)
