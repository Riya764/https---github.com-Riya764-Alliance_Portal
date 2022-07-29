'''
enums for all the apps
'''
from http.client import PARTIAL_CONTENT
from django.db.models.fields import BLANK_CHOICE_DASH


class SentStatusType(object):
    '''
    Enum for sent status Type
    '''
    PENDING = 1
    INPROGRESS = 2
    SUCCESS = 3
    ERROR = 4
    FLIGHT = 5

    STATUS = (
        (PENDING, 'PENDING'),
        (INPROGRESS, 'INPROGRESS'),
        (SUCCESS, 'SUCCESS'),
        (ERROR, 'ERROR'),
        (FLIGHT, 'NOTIFICATIONS OFF'),
    )


class OrderStatus(object):
    '''
    Enum for order status Type
    '''
    ORDERED = 1
    CONFIRMED = 2
    SHIPPED = 3
    READYPICKUP = 4
    DISPATCHED = 5
    DELIVERED = RECEIVED = 6
    CANCELLED = 7
    DISCARDED = 8
    RETURNED = 9
    INTRANSIT = 10
    PARTIAL_RETURN=11


    LABEL = {
        ORDERED: 'ORDERED',
        CONFIRMED: 'CONFIRMED',
        SHIPPED: 'SHIPPED',
        READYPICKUP: 'READY FOR PICKUP',
        DISPATCHED: 'DISPATCHED',
        CANCELLED: 'CANCELLED',
        DELIVERED: 'DELIVERED',
        RETURNED: 'RETURNED',
        PARTIAL_RETURN:'PARTIAL_RETURN',
        DISCARDED: 'DISCARDED',
        INTRANSIT: 'IN TRANSIT',
        RECEIVED: 'RS RECEIVED'

    }

    STATUS = (
        (ORDERED, LABEL[ORDERED]),
        (DISPATCHED, LABEL[DISPATCHED]),
        (CANCELLED, LABEL[CANCELLED]),
        (RETURNED, LABEL[RETURNED]),
        (PARTIAL_RETURN, LABEL[PARTIAL_RETURN])
    )

    APSTATUS = (
        (ORDERED, LABEL[ORDERED]),
        (INTRANSIT, LABEL[INTRANSIT]),
        (CANCELLED, LABEL[CANCELLED]),
        (RECEIVED, LABEL[RECEIVED]),
    )
    CHOICES_AND_EMPTY_CHOICE = BLANK_CHOICE_DASH + list(STATUS)
    CHOICES_AP_AND_EMPTY_CHOICE = BLANK_CHOICE_DASH + list(APSTATUS)


class PaymentStatus(object):
    '''
    Enum for sent status Type
    '''
    PENDING = 1
    PAID = 2

    PAYMENTSLABEL = {
        PENDING: 'PENDING',
        PAID: 'PAID'
    }

    STATUS = (
        (PENDING, 'PENDING'),
        (PAID, 'PAID'),
    )

    CHOICES_AND_EMPTY_CHOICE = BLANK_CHOICE_DASH + list(STATUS)


class ClaimStatus(object):
    '''
    Enum for sent status Type
    '''
    NONE = 0
    PENDING = 1
    PROCESSED = 2

    LABEL = {
        NONE: 'NA',
        PENDING: 'PENDING',
        PROCESSED: 'PROCESSED'
    }

    STATUS = (
        (NONE, 'NA'),
        (PENDING, 'PENDING'),
        (PROCESSED, 'PROCESSED'),
    )


class CancelOrderReasons(object):
    '''
    Enum for CancelOrderReasons
    '''
    SHAKTICANCEL = 1
    CREDITBLOCK = 2
    DELIVERYDELAYED = 3
    INCORRECTORDER = 4
    OTHER = 5

    STATUS = (
        (SHAKTICANCEL, 'Shakti Cancelled the order'),
        (CREDITBLOCK, 'Credit Block'),
        (DELIVERYDELAYED, 'Delivery Delayed'),
        (INCORRECTORDER, 'Incorrect Order'),
        (OTHER, 'Other'),
    )


class OtpStatusType(object):
    '''
     Enum
    '''
    # Unused OTP
    PENDING = 0
    # Used OTP
    VERIFIED = 1
    # Sent successfully
    SUCCESS = 2
    # Error sending OTP
    ERROR = 3
    # Used by user
    USED = 4

    STATUS = {
        (PENDING, 'PENDING'),
        (VERIFIED, 'VERIFIED'),
        (SUCCESS, 'SUCCESS'),
        (ERROR, 'ERROR'),
        (USED, 'USED'),
    }


class AddressType(object):
    '''
    Enum for sent status Type
    '''
    SENDER = 'sender'
    RECEPIENT = 'recepient'

    STATUS = {
        (SENDER, 'SENDER'),
        (RECEPIENT, 'RECEPIENT'),
    }


class UserType(object):
    '''
    Enum for user Type
    '''
    ALLIANCE = 1
    DISTRIBUTOR = 2
    SALES = 3
    SHAKTIENTERPRENEUR = 4
    GENERAL = 5

    STATUS = (
        (ALLIANCE, 'Alliance Partner'),
        (DISTRIBUTOR, 'Regional Distributor'),
        (SALES, 'Regional Sales Promoter'),
        (SHAKTIENTERPRENEUR, 'Shakti Entrepreneur'),
        (GENERAL, 'Super User'),
    )


class OrderDay(object):
    '''
    Enum for OrderDay
    '''
    SUNDAY = 1
    MONDAY = 2
    TUESDAY = 3
    WEDNESDAY = 4
    THURSDAY = 5
    FRIDAY = 6
    SATURDAY = 7
    NO_ORDER_DAY = 8

    STATUS = (
        (NO_ORDER_DAY, '---'),
        (MONDAY, 'MONDAY'),
        (TUESDAY, 'TUESDAY'),
        (WEDNESDAY, 'WEDNESDAY'),
        (THURSDAY, 'THURSDAY'),
        (FRIDAY, 'FRIDAY'),
        (SATURDAY, 'SATURDAY'),
        (SUNDAY, 'SUNDAY'),
    )

    LABEL = {
        NO_ORDER_DAY: '---',
        MONDAY: 'MONDAY',
        TUESDAY: 'TUESDAY',
        WEDNESDAY: 'WEDNESDAY',
        THURSDAY: 'THURSDAY',
        FRIDAY: 'FRIDAY',
        SATURDAY: 'SATURDAY',
        SUNDAY: 'SUNDAY',
    }


class OrderType(object):
    '''
    Enum for OrderDay
    '''
    PRIMARY = 1
    SECONDARY = 2

    STATUS = (
        (PRIMARY, 'Primary Orders'),
        (SECONDARY, 'Secondary Orders'),
    )


class PriceRange(object):
    ''' PRice Range order filter'''
    ZERO = 0
    ONE = 1000
    TWO = 5000
    THREE = 10000
    FOUR = 50000
    FIVE = 100000

    STATUS = (
        (ZERO, 0),
        (ONE, 1000),
        (TWO, 5000),
        (THREE, 10000),
        (FOUR, 50000),
        (FIVE, 100000),
    )

    CHOICES_AND_EMPTY_CHOICE = BLANK_CHOICE_DASH + list(STATUS)
