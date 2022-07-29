'''Job admin'''
from django.contrib import admin
from hul.utility import CustomAdminTitle
from job.models import Email, MobileNotification

class EmailAdmin(CustomAdminTitle):
    '''
    list columns of email
    '''
    list_display = ['from_email', 'to_email',
                    'subject', 'sent_status_type', 'sent_date']

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False

class SmsAdmin(CustomAdminTitle):
    '''
    list columns of Sms model
    '''
    list_display = ['to_phone', 'display_invoice', 'display_shakti_name',
                    'order_status', 'message', 'sent_status_type', 'sent_date']

    def display_invoice(self, obj):
        ''' get invoice number '''
        return obj.distributor_order.invoice_number
    display_invoice.short_description = 'Invoice Number'

    def display_shakti_name(self, obj):
        ''' get shakti name '''
        return obj.distributor_order.shakti_enterpreneur.name
    display_invoice.short_description = 'Shakti Enterpreneur'

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_add_permission(self, request, obj=None):
        return False

admin.site.register(Email, EmailAdmin)
admin.site.register(MobileNotification, SmsAdmin)
