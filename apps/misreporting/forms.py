''' Form '''
from django import forms
from django.utils import timezone
from django.forms import ModelMultipleChoiceField
from django.contrib.admin.widgets import AdminDateWidget, FilteredSelectMultiple
from django.forms.widgets import SelectDateWidget
from app.models import (AlliancePartner, RegionalDistributor,
                        ShaktiEntrepreneur, RegionalSalesPromoter, UserAddress)
from moc.models import MoCMonth
from hul.choices import OrderType, PriceRange, OrderStatus, PaymentStatus
from localization.models import State, Country


class MyRSPField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return "{0} : {1}".format(obj.rsp_id, obj.user.name)


class MyRSPFieldS(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{0} : {1}".format(obj.rsp_id, obj.user.name)


class DatefieldsForm(forms.Form):
    ''' includes date fields '''
    start_date = forms.DateField(required=False,
                                 widget=AdminDateWidget(attrs={'class': 'clear vDateField',
                                                               'readonly': 'true'}
                                                        )
                                 )
    end_date = forms.DateField(required=False,
                               widget=AdminDateWidget(attrs={'class': 'clear vDateField',
                                                             'readonly': 'true'}
                                                      )
                               )

    moc = forms.ModelMultipleChoiceField(
        label="Select Moc",
        queryset=MoCMonth.objects.filter(
            start_date__lte=timezone.now().date()),
        widget=forms.SelectMultiple(attrs={'class': 'clear'}),
        required=False,
    )


class StateForm(forms.Form):
    '''Multiple select states'''
    state = forms.ModelMultipleChoiceField(
        label="State",
        queryset=State.objects.filter(
            state__isnull=False).distinct().order_by('name'),
        widget=forms.SelectMultiple(attrs={'class': 'clear'}),
        required=False,
    )


class AlliancePartnerForm(forms.Form):
    '''AlliancePartner Form'''

    alliance_partner = forms.ModelChoiceField(
        label="Alliance Partner",
        queryset=AlliancePartner.objects.all().filter(
            is_active=True).order_by('user__name'),
        widget=forms.Select(attrs={'class': 'clear'}),
        required=False,
        to_field_name="user_id"
    )


class BasePackLevelForm(DatefieldsForm, StateForm, AlliancePartnerForm):

    field_order = ['start_date', 'end_date',
                   'moc', 'state', 'alliance_partner']


class BillCountDataForm(DatefieldsForm, StateForm, AlliancePartnerForm):

    field_order = ['start_date', 'end_date',
                   'moc', 'state', 'alliance_partner']


class SeLevelForm(DatefieldsForm, StateForm, AlliancePartnerForm):

    redistribution_stockist = forms.ModelMultipleChoiceField(
        label='Redistribution Stockist',
        required=False, to_field_name='user_id',
        queryset=RegionalDistributor.objects.select_related(
            'user').filter(is_active=True).order_by('user__name'),
        widget=forms.SelectMultiple(attrs={'class': 'clear'})
    )

    shakti_enterpreneur = forms.ModelChoiceField(
        label='Shakti Enterpreneur',
        required=False, to_field_name='user_id',
        queryset=ShaktiEntrepreneur.objects.select_related(
            'user').filter(is_active=True).order_by('user__name'),
        widget=forms.Select(attrs={'class': 'clear'})
    )

    field_order = ['alliance_partner', 'redistribution_stockist', 'shakti_enterpreneur',
                   'state', 'start_date', 'end_date', 'moc']


class RspLevelFilterForm(DatefieldsForm, StateForm, AlliancePartnerForm):
    ''' rsp level filter '''

    sales_promoter = MyRSPFieldS(label='Rural Sales Promoter', required=False,
                                 queryset=RegionalSalesPromoter.objects.select_related('user').filter(is_active=True).order_by('user__name'), to_field_name="user_id",
                                 widget=forms.Select(attrs={'class': 'clear'}))
    field_order = ['alliance_partner', 'sales_promoter',
                   'state', 'start_date', 'end_date', 'moc']


class RsLevelFilterForm(DatefieldsForm):
    ''' rsp level filter '''

    redistribution_stockist = forms.ModelChoiceField(required=False,
                                                     queryset=RegionalDistributor.objects.select_related('user').filter(is_active=True).order_by('user__name'), to_field_name="user_id",
                                                     widget=forms.Select(attrs={'class': 'clear'}))
    field_order = ['redistribution_stockist', 'start_date', 'end_date']


class AdvanceOrderFilterForm(DatefieldsForm):
    '''filter form'''

    order_type = forms.CharField(widget=forms.RadioSelect(choices=OrderType.STATUS),
                                 initial=1, help_text="", max_length=128)
    order_number = forms.CharField(label='Invoice Number', required=False, max_length=50,
                                   widget=forms.TextInput(
                                       attrs={'class': 'clear'})
                                   )
    brand = forms.ModelChoiceField(required=False,
                                   queryset=AlliancePartner.objects.select_related('user').filter(
                                       is_active=True).order_by('user__name'),
                                   to_field_name="user_id",
                                   widget=forms.Select(attrs={'class': 'clear'}))
    redistribution_stockist = forms.ModelMultipleChoiceField(required=False,
                                                             queryset=RegionalDistributor.objects.select_related('user').filter(is_active=True).order_by('user__name'), to_field_name="user_id",
                                                             widget=forms.SelectMultiple(attrs={'class': 'clear'}))
    sales_promoter = MyRSPField(label='Rural Sales Promoter', required=False,
                                queryset=RegionalSalesPromoter.objects.select_related(
                                    'user').filter(is_active=True).order_by('user__name'),
                                to_field_name="user_id",
                                widget=forms.SelectMultiple(attrs={'class': 'clear'}))
    # shakti_enterpreneur = forms.ModelMultipleChoiceField(required=False,
    #                                                      queryset=ShaktiEntrepreneur.objects.select_related('user').filter(is_active=True).order_by('user__name'), to_field_name="user_id",
    # widget=forms.SelectMultiple(attrs={'class': 'clear'}))
    payment_status = forms.ChoiceField(label='Payment Status',
                                       choices=PaymentStatus.CHOICES_AND_EMPTY_CHOICE,
                                       help_text="",
                                       required=False, widget=forms.Select(attrs={'class': 'clear'}))
    order_status = forms.ChoiceField(label='Order Status',
                                     choices=OrderStatus.CHOICES_AND_EMPTY_CHOICE,
                                     help_text="",
                                     required=False, widget=forms.Select(attrs={'class': 'clear'}))
    order_status_ap = forms.ChoiceField(label='Order Status',
                                        choices=OrderStatus.CHOICES_AP_AND_EMPTY_CHOICE,
                                        help_text="",
                                        required=False, widget=forms.Select(attrs={'class': 'clear'}))

    start_amount = forms.ChoiceField(label='Minimum amount',
                                     choices=PriceRange.CHOICES_AND_EMPTY_CHOICE,
                                     initial=PriceRange.ZERO,
                                     required=False, widget=forms.Select(attrs={'class': 'clear'}))
    end_amount = forms.ChoiceField(label='Maximum amount',
                                   choices=PriceRange.CHOICES_AND_EMPTY_CHOICE,
                                   initial=PriceRange.FIVE, help_text="",
                                   required=False, widget=forms.Select(attrs={'class': 'clear'}))

    field_order = ['order_type', 'order_type', 'order_type', 'order_number', 'brand', 'redistribution_stockist',
                   'sales_promoter', 'shakti_enterpreneur', 'payment_status', 'order_status', 'start_amount', 'end_amount',
                   'start_date', 'end_date', 'moc']

    # class Media:
    #     css = {'all': ('/admin/css/widgets.css',), }
    #     js = ('/admin/jsi18n/',)

    # def __init__(self, parents=None, *args, **kwargs):
    #     super(AdvanceOrderFilterForm, self).__init__(*args, **kwargs)
