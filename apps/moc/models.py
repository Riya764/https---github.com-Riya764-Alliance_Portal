from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from hul.utility import TimeStamped


@python_2_unicode_compatible
class MoCYear(models.Model):
    """Model definition for MoCYear."""

    name = models.CharField(max_length=50)
    year = models.PositiveIntegerField('MoC Year', unique=True)

    class Meta:
        """Meta definition for MoC Year."""

        verbose_name = 'MoC Year'
        verbose_name_plural = 'MoC Years'

    def __str__(self):
        """Unicode representation of MoCYear."""
        return self.name

    def save(self, *args, **kwargs):
        self.name = 'MoC ' + str(self.year)
        # Call the real save() method
        return super(MoCYear, self).save(*args, **kwargs)

    # @staticmethod
    # def autocomplete_search_fields():
    #     return 'name'


@python_2_unicode_compatible
class MoCMonth(TimeStamped):
    """Model definition for MoCMonth."""

    name = models.CharField(max_length=50)
    moc_year = models.ForeignKey(
        MoCYear, related_name='moc_year', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        """Meta definition for MoCMonth."""

        verbose_name = 'MoC Month'
        verbose_name_plural = 'MoC Months'
        ordering = ('-start_date', 'moc_year')

    def __str__(self):
        """Unicode representation of MoCMonth."""
        return "{0}-{1}".format(self.name,self.moc_year.year)

    # @staticmethod
    # def autocomplete_search_fields():
    #     return 'moc_year'
