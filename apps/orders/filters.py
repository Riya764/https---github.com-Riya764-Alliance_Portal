''' orders/filters.py '''
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


from hul.choices import OrderStatus
from app.models import (RegionalSalesPromoter, RegionalDistributor,
                        AlliancePartner)


class OrderStatusFilter(admin.SimpleListFilter):
    '''
    Order status filter for orders
    '''
    title = _('Order Status')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'order_status'

    def lookups(self, request, model_admin):
        """
        Initial set of values for filter.
        """
        return OrderStatus.APSTATUS

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value():
            queryset = queryset.filter(order_status=self.value())
        return queryset

class SecondaryOrderStatusFilter(admin.SimpleListFilter):
    '''
    Order status filter for orders
    '''
    title = _('Order Status')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'order_status'

    def lookups(self, request, model_admin):
        """
        Initial set of values for filter.
        """
        return OrderStatus.STATUS

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value():
            queryset = queryset.filter(order_status=self.value())
        return queryset

class PromoterFilter(admin.SimpleListFilter):
    '''
    Promoter filter to filter orders at promoter level
    '''
    title = _('RSP')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'promoter'
    default_value = None

    def lookups(self, request, model_admin):
        """
        Initial set of values for filter.
        """
        list_of_promoters = []
        if request.user.is_superuser:
            queryset = RegionalSalesPromoter.objects.select_related(
                'user').all()
        else:
            distributor = RegionalDistributor.objects.filter(
                user=request.user).first()
            queryset = RegionalSalesPromoter.objects.filter(
                regional_distributor=distributor).select_related('user')

        for promoter in queryset:
            list_of_promoters.append(
                (str(promoter.user_id), promoter.rsp_id)
            )
        return sorted(list_of_promoters, key=lambda tp: tp[1])

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # to decide how to filter the queryset.
        if self.value():
            return queryset.filter(sales_promoter_id=self.value())
        return queryset


class DistributorFilter(admin.SimpleListFilter):
    '''
    order filter through distributor
    '''
    title = _('Redistribution Stockist')

    parameter_name = 'distrubtor'

    def lookups(self, request, model_admin):
        """
        Initial set of values for filter.
        """
        distributors_list = []
        if request.user.is_superuser:
            queryset = RegionalDistributor.objects.select_related('user').all()
        else:
            alliance_partner = AlliancePartner.objects.filter(
                user=request.user).first()
            queryset = RegionalDistributor.objects.filter(
                alliance_partner=alliance_partner).select_related('user')
        for distributor in queryset:
            distributors_list.append(
                (str(distributor.user_id), distributor.user.name)
            )
        return sorted(distributors_list, key=lambda tp: tp[1])

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value():
            return queryset.filter(distributor_id=self.value())
        return queryset


class AllianceFilter(admin.SimpleListFilter):
    '''
    order filter through Alliances
    '''
    title = _('Alliance Partners')

    parameter_name = 'alliance'

    def lookups(self, request, model_admin):
        """
        Initial set of values for filter.
        """
        alliance_list = []
        queryset = AlliancePartner.objects.select_related('user').all()

        for alliance in queryset:
            alliance_list.append(
                (str(alliance.user_id), alliance.user.name)
            )
        return sorted(alliance_list, key=lambda tp: tp[1])

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value():
            return queryset.filter(alliance_id=self.value())
        return queryset


class RangeTextInputFilter(admin.ListFilter):
    """
    renders filter form with text input and submit button
    """
    parameter_name = None
    template = "admin/filters/textinput_filter.html"

    def __init__(self, request, params, model, model_admin):
        self._start_field_name = '%s_1' % self.parameter_name
        self._end_field_name = '%s_2' % self.parameter_name
        super(RangeTextInputFilter, self).__init__(
            request, params, model, model_admin)
        if self.parameter_name is None:
            raise ImproperlyConfigured(
                "The list filter '%s' does not specify "
                "a 'parameter_name'." % self.__class__.__name__)

        if self._start_field_name in params and self._end_field_name in params:
            start = params.pop(self._start_field_name)
            end = params.pop(self._end_field_name)
            self.used_parameters[self.parameter_name] = [start, end]

    def value(self):
        """
        Returns the value (in string format) provided in the request's
        query string for this filter, if any. If the value wasn't provided then
        returns None.
        """
        return self.used_parameters.get(self.parameter_name, None)

    def has_output(self):
        return True

    def expected_parameters(self):
        """
        Returns the list of parameter names that are expected from the
        request's query string and that will be used by this filter.
        """
        return [self._start_field_name, self._end_field_name]

    def choices(self, cl):
        all_choice = {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self._start_field_name, self._end_field_name]),
            'display': _('All'),
        }
        return ({
            'get_query': cl.params,
            'current_value': self.value(),
            'all_choice': all_choice,
            'parameter_name': self.parameter_name,
            'filter_params': [self._start_field_name, self._end_field_name]
        }, )
