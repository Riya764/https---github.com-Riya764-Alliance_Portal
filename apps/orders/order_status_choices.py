'''
order status choices with disabled attribute
'''
from hul.choices import OrderStatus


class OrderStatusChoices(object):
    ''' class that will have disabled choices list and related function '''

    DISABLED = {
        OrderStatus.ORDERED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DELIVERED,
            OrderStatus.RETURNED,
        ],
        OrderStatus.CONFIRMED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DISPATCHED,
            OrderStatus.DELIVERED,
            OrderStatus.RETURNED,
        ],
        OrderStatus.DISPATCHED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DISPATCHED,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.DELIVERED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DISPATCHED,
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
            OrderStatus.RECEIVED,
        ],
        OrderStatus.RECEIVED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DISPATCHED,
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
            OrderStatus.RECEIVED,
        ],
        OrderStatus.RETURNED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DISPATCHED,
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
            OrderStatus.RETURNED,
        ],
        OrderStatus.CANCELLED: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.DISPATCHED,
            OrderStatus.CANCELLED,
            OrderStatus.DELIVERED,
            OrderStatus.RETURNED,
        ],
        OrderStatus.INTRANSIT: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
            OrderStatus.CANCELLED,
        ]
    }

    DISABLED_PRIMARY = {
        OrderStatus.ORDERED: [
            OrderStatus.ORDERED,
            OrderStatus.DELIVERED,
            OrderStatus.INTRANSIT,
            OrderStatus.CANCELLED,
            OrderStatus.RETURNED,
        ],
        OrderStatus.CONFIRMED: DISABLED[OrderStatus.CONFIRMED],
        OrderStatus.DISPATCHED: DISABLED[OrderStatus.DISPATCHED],
        OrderStatus.DELIVERED: DISABLED[OrderStatus.DELIVERED],
        OrderStatus.RECEIVED: DISABLED[OrderStatus.RECEIVED],
        OrderStatus.RETURNED: DISABLED[OrderStatus.RETURNED],
        OrderStatus.CANCELLED: DISABLED[OrderStatus.CANCELLED],
        OrderStatus.INTRANSIT: [
            OrderStatus.ORDERED,
            OrderStatus.INTRANSIT,
        ],
    }

    def get_disabled_choices(self, current_status=OrderStatus.ORDERED, statuses=OrderStatus.STATUS, order_type='secondary'):
        ''' disable status according to current status '''
        if order_type == 'secondary':
            disabled_list = self.DISABLED[current_status]
        elif order_type == 'primary':
            disabled_list = self.DISABLED_PRIMARY[current_status]
                
        modified_status = list(statuses)
        index = 0
        for status in modified_status:
            status_lst = list(status)
            if status_lst[0] in disabled_list:
                status_lst[1] = {'disabled': True, 'label': status_lst[1]}
                modified_status[index] = tuple(status_lst)
            index += 1

        return tuple(modified_status)
