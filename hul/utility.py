'''
utitlity for all the apps
'''
import uuid
from django.contrib import admin
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import models
from dateutil import relativedelta
from rest_framework import status
from hul.choices import OrderStatus
from hul.constants import (STATUS_CODE_KEY, MESSAGE_KEY,
                           HTTP_USER_ERROR, ERROR_KEY, RESPONSE_KEY, MOC_START_DATE, MOC_END_DATE)


class HulUtility(object):
    '''HulUtility'''

    @staticmethod
    def random_token():
        '''
        Generate the n digits random number.
        Args:
            digits: the number of digits.
        Returns:
            the n digit number.
        '''
        uid = uuid.uuid4()

        return uid.hex

    @staticmethod
    def expire_token(lst_acces_token):
        '''  Expire old token '''
        count = 0
        for access_token in lst_acces_token:
            if not access_token.is_expired():
                access_token.expires = timezone.now()
                access_token.save()
                count = count + 1
        return count

    @staticmethod
    def data_wrapper(response=None, status_code=status.HTTP_200_OK, message=''):
        '''data wrapper for response'''
        response_dic = {}
        response_dic[STATUS_CODE_KEY] = status_code
        response_dic[MESSAGE_KEY] = message
        if HTTP_USER_ERROR == status_code:
            response_dic[ERROR_KEY] = response
        else:
            response_dic[RESPONSE_KEY] = response

        return response_dic

    @staticmethod
    def week_range(date):
        """Find the first/last day of the week for the given day.
        Assuming weeks start on Sunday and end on Saturday.

        Returns a tuple of ``(start_date, end_date)``.

        """
        # isocalendar calculates the year, week of the year, and day of the week.
        # dow is Mon = 1, Sat = 6, Sun = 7
        year, week, dow = date.isocalendar()

        # Find the first day of the week.
        if dow == 7:
            # Since we want to start with Sunday, let's test for that
            # condition.
            start_date = date
        else:
            # Otherwise, subtract `dow` number days to get the first day
            start_date = date - timedelta(dow)

        # Now, add 6 for the last day of the week (i.e., count up to Saturday)
        end_date = start_date + timedelta(6)

        return (start_date, end_date)


class TimeStamped(models.Model):
    '''
    Model used as base class for Time stamp.
    Used as base class for other models.
    '''
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class CustomAdminTitle(admin.ModelAdmin):
    '''Custom Admin to change text "Change" to "Edit"'''

    def change_view(self, request, object_id, form_url='', extra_context=None):
        if not extra_context:
            extra_context = {}
        add = object_id is None
        extra_context['title'] = (_('Add %s') if add else _('Edit %s'))\
            % force_text(self.model._meta.verbose_name)
        return super(CustomAdminTitle, self).change_view(request,
                                                         object_id,
                                                         form_url,
                                                         extra_context)

    def changelist_view(self, request, extra_context=None):
        '''Custom Admin to change text "Change" to "Edit"'''
        if not extra_context:
            extra_context = {}
        extra_context['title'] = _('Select %s to edit ')\
            % force_text(self.model._meta.verbose_name)
        return super(CustomAdminTitle, self).changelist_view(request,
                                                             extra_context)


class NoAdminTitle(admin.ModelAdmin):
    '''Custom Admin to change text "Change" to "Edit"'''

    def changelist_view(self, request, extra_context=None):
        '''Custom Admin to change text "Change" to "Edit"'''
        if not extra_context:
            extra_context = {}
        extra_context['title'] = _('%s')\
            % force_text(self.model._meta.verbose_name)
        return super(NoAdminTitle, self).changelist_view(request,
                                                         extra_context)


class MOC(object):
    '''
    calculate MOC
    '''
    @staticmethod
    def calculate_moc(start_date, end_date, order_data):
        '''
        differnce between start date and end date
        if less than 12 months return number
        else calculate moc year + month wise
        '''
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        #start_date = order_data[0].dispatched_on.date() if order_data[0].dispatched_on else order_data[0].created.date()
        start_date = order_data[0].created.date()
        if start_date.day < MOC_START_DATE:
            days = MOC_START_DATE - start_date.day
            moc1_end = start_date + timedelta(days)
        else:
            days = MOC_END_DATE - start_date.day
            next_month = MOC.addmonths(start_date, 1)
            moc1_end = next_month + timedelta(days)
        moc_data = []

        moc_start = start_date
        totals = order_data.count()
        counter = 0
        rsp_dict = {}
        main_data = []
        #start, end = mocs
        for order in order_data:
            if order.sales_promoter_id not in rsp_dict.keys():
                rsp_dict[order.sales_promoter_id] = {}
                rsp_dict[order.sales_promoter_id]['sales_promoter'] = order.sales_promoter.name
                rsp_dict[order.sales_promoter_id]['moclist'] = []
                rsp_dict[order.sales_promoter_id]['grand_total'] = 0
                rsp_dict[order.sales_promoter_id]['ordered_total'] = 0
                rsp_dict[order.sales_promoter_id]['dispatched_total'] = 0
            moc_data = rsp_dict[order.sales_promoter_id]['moclist']

            rsp_dict[order.sales_promoter_id]['grand_total'] += order.total_amount

            if order.order_status == OrderStatus.ORDERED:
                rsp_dict[order.sales_promoter_id]['ordered_total'] += order.total_amount
            else:
                rsp_dict[order.sales_promoter_id]['dispatched_total'] += order.total_amount

            # if order.dispatched_on is not None:
            #     if order.dispatched_on.date() < moc1_end:
            #         moc_data, moc_start = MOC.append_order(moc_data, counter, order)
            #     else:
            #         counter+= 1
            #         moc1_end = MOC.addmonths(moc_start, 1)
            #         moc_data, moc_start = MOC.append_order(moc_data, counter, order)

            # el

            if order.created.date() < moc1_end:
                moc_data, moc_start = MOC.append_order(
                    moc_data, counter, order)
            else:
                counter += 1
                moc1_end = MOC.addmonths(moc_start, 1)
                moc_data, moc_start = MOC.append_order(
                    moc_data, counter, order)

            rsp_dict[order.sales_promoter_id]['moclist'] = moc_data
        for moc in rsp_dict:
            main_data.append(rsp_dict[moc])
        return main_data

    @staticmethod
    def append_order(moc_data, counter,  order):
        default_moc = []
        addnew = False
        try:
            moc_data_cn = moc_data[counter]
        except IndexError:
            moc_data_cn = default_moc
            addnew = True

        moc_data_cn.append(order)
        moc_start = order.created.date()
        # if order.dispatched_on is not None:
        #     moc_start = order.dispatched_on.date()

        if addnew:
            moc_data.append(moc_data_cn)
        else:
            moc_data[counter] = moc_data_cn
        return moc_data, moc_start

    @staticmethod
    def addmonths(date, months):
        targetmonth = months+date.month
        newdate = datetime.now().date()
        try:
            newdate = date.replace(
                year=date.year+int(targetmonth/12), month=(targetmonth % 12))
        except:
            # There is an exception if the day of the month we're in does not exist in the target month
            # Go to the FIRST of the month AFTER, then go back one day.
            newdate = date.replace(
                year=date.year+int((targetmonth+1)/12), month=((targetmonth+1) % 12), day=1)
            newdate += timedelta(days=-1)
        return newdate
