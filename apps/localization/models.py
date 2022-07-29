from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from hul.utility import TimeStamped


@python_2_unicode_compatible
class Country(TimeStamped):
    """
    model for country
    """
    name = models.CharField(max_length=200)
    phone_code = models.CharField(max_length=10, blank=True, null=True)
    country_code = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(object):
        """
        inner class
        """
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'


@python_2_unicode_compatible
class State(TimeStamped):
    """
    model for country
    """
    country = models.ForeignKey(Country)
    name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(object):
        """
        inner class
        """
        verbose_name = 'State'
        verbose_name_plural = 'States'


@python_2_unicode_compatible
class City(TimeStamped):
    """
    model for country
    """
    country = models.ForeignKey(Country)
    state = models.ForeignKey(State)
    name = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(object):
        """
        inner class
        """
        verbose_name = 'City'
        verbose_name_plural = 'Cities'


@python_2_unicode_compatible
class MeasurementUnit(TimeStamped):
    """
    model for Measurement Unit
    """
    unit = models.CharField(max_length=50)

    def __str__(self):
        return self.unit
