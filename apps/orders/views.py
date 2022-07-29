'''ORDER/view.py'''
import json
from django.views.decorators.http import require_http_methods
from django.http import Http404, HttpResponse, JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone as dt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.template.response import TemplateResponse
from django.shortcuts import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.db.models import Sum

from easy_pdf.views import PDFTemplateView

from django.views.generic import TemplateView
from product.models import Product
from hul.settings.common import ADMIN_SITE_HEADER
from hul.choices import OrderStatus
from hul.constants import DISPATCH_DAYS
from app.models import ShaktiEntrepreneur, RegionalDistributor, AlliancePartner
from orders.models import (DistributorOrderDetail, AlliancePartnerOrderDetail,
                           DistributorOrder, AlliancePartnerOrder, DistributorStock)
from orders.lib.order_management import OrderManagement
from orders.lib.create_distributor_order import DispatchDistributorOrder
from offers.models import PromotionLines, DiscountType
from .invoices import DistributorInvoice

class DistributerOrderInvoiceView(PDFTemplateView):
    '''Distributer Order Invoice'''
    # template_name = "distributor_order_invoice.html"
    template_name = "distributor_pepsico.html"

    def get(self, request, *args, **kwargs):
        """
        Handles GET request and returns HTTP response.
        """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context_data = super(DistributerOrderInvoiceView,
                             self).get_context_data(*args, **kwargs)

        try:
            if self.request.user.is_superuser:
                distributor_order = DistributorOrder.objects.filter(
                    id=self.kwargs['order_invoice']).get()
            else:
                distributor_order = DistributorOrder.objects.filter(
                    id=self.kwargs['order_invoice'], distributor=self.request.user.pk).get()

            distributor_order_details = list(DistributorOrderDetail.objects.filter(
                distributor_order=self.kwargs['order_invoice'],
                item_status=OrderStatus.DISPATCHED, dispatch_quantity__gt=0).select_related('product'))

            for order in distributor_order_details:
                order.mrp = order.product.mrp
                cases, units = DistributorInvoice.get_cases_units(
                    order.product.cld_configurations, order.dispatch_quantity)
                order.units = units
                order.cases = cases
                order.taxable_amount = order.price - \
                    (order.discount_amount or 0.0) - order.distributor_discount

            shakti_address = ShaktiEntrepreneur.objects.filter(
                user=distributor_order.shakti_enterpreneur.id).first()
            invoiced_to = {}
            invoiced_to['name'] = distributor_order.shakti_enterpreneur.name
            invoiced_to['code'] = distributor_order.shakti_enterpreneur.shakti_user.code
            invoiced_to['contact_number'] = distributor_order.shakti_enterpreneur.contact_number
            if shakti_address:
                invoiced_to['address'] = shakti_address.address
            else:
                invoiced_to['address'] = ''

            rd_address = distributor_order.distributor.regionaldistributor.address
            invoiced_from = {}
            invoiced_from['name'] = distributor_order.distributor.name
            invoiced_from['contact_number'] = distributor_order.distributor.contact_number
            invoiced_from['address'] = rd_address or ''
            invoiced_from['gst_code'] = distributor_order.distributor.regionaldistributor.gst_code

            context_data.update({
                'site_title': _(ADMIN_SITE_HEADER),
                'title': _("Order Summary"),
                'order_details': distributor_order_details,
                'order': distributor_order,
                'logo': distributor_order.shakti_enterpreneur.image,
                'invoiced_to': invoiced_to,
                'invoiced_from': invoiced_from
            })

        except:
            raise Http404
        return context_data


class AllianceOrderInvoiceView(PDFTemplateView):
    '''Alliance Order Invoice'''
    # template_name = "alliance_order_invoice.html"
    template_name = "alliance_pepsico.html"

    def get(self, request, *args, **kwargs):
        """
        Handles GET request and returns HTTP response.
        """
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, *args, **kwargs):
        context_data = super(AllianceOrderInvoiceView,
                             self).get_context_data(*args, **kwargs)
        try:
            alliance_order = AlliancePartnerOrder.objects.filter(
                id=self.kwargs['order_invoice'])
            if not self.request.user.is_superuser and hasattr(self.request.user, 'regionaldistributor'):
                alliance_order = alliance_order.filter(
                    distributor=self.request.user.pk)
            alliance_order = alliance_order[0]
            alliance_order_details = list(AlliancePartnerOrderDetail.objects.filter(
                alliance_partner_order=alliance_order.pk, item_status__in=[OrderStatus.INTRANSIT, OrderStatus.RECEIVED]).select_related('product'))

            for order in alliance_order_details:
                order.mrp = order.product.mrp
                cases, units = DistributorInvoice.get_cases_units(
                    order.product.cld_configurations, order.dispatch_quantity or order.quantity
                )
                order.units = units
                order.cases = cases
                order.tax_amount = order.price - order.discount_amount
                order.net_amount = order.tax_amount + order.cgst_amount + \
                    order.sgst_amount + order.igst_amount

            # claim discounts
            claim_amount = 0
            if hasattr(alliance_order, 'alliancepartnershaktidiscount_set'):
                shakti_discount = alliance_order.alliancepartnershaktidiscount_set.aggregate(
                    shakti_discount=Sum('discount_amount'))
                claim_amount += shakti_discount['shakti_discount'] or 0

            if hasattr(alliance_order, 'alliancepartnerdiscountdetail_set'):
                discount = alliance_order.alliancepartnerdiscountdetail_set.aggregate(
                    discount=Sum('discount_amount'))
                claim_amount += discount['discount'] or 0
            alliance_order.claim_amount = claim_amount
            alliance_order.grand_total = alliance_order.total_amount - claim_amount

            rd_address = RegionalDistributor.objects.filter(
                user=alliance_order.distributor.id).first()
            invoiced_to = {}
            invoiced_to['name'] = alliance_order.distributor.name
            invoiced_to['contact_number'] = alliance_order.distributor.contact_number
            if rd_address:
                invoiced_to['address'] = rd_address.address
                invoiced_to['gst_code'] = rd_address.gst_code
            else:
                invoiced_to['address'] = ''
                invoiced_to['gst_code'] = ''

            ap_address = AlliancePartner.objects.filter(
                user=alliance_order.alliance.pk).first()
            invoiced_from = {}
            invoiced_from['name'] = alliance_order.alliance.name
            invoiced_from['contact_number'] = alliance_order.alliance.contact_number
            if ap_address:
                invoiced_from['address'] = ap_address.address
            else:
                invoiced_from['address'] = ''

            context_data.update({
                'site_title': ADMIN_SITE_HEADER,
                'title': "Order Summary",
                'order_details': alliance_order_details,
                'order': alliance_order,
                'logo': alliance_order.alliance.image,
                'invoiced_to': invoiced_to,
                'invoiced_from': invoiced_from
            })

            if invoiced_from["name"] == 'Pidilite Industries Limited':
                self.template_name = "alliance_pidilite.html"

        except:
            raise Http404
        return context_data


@login_required
@user_passes_test(lambda u: u.is_staff)
def dispatch_stockist_order(request, order_id):
    '''
    dispatch RS order to SE and do quantity changes
    '''
    redirect_url = reverse('admin:orders_distributororder_changelist')

    try:
        referer = request.META['HTTP_REFERER']
    except:
        referer = redirect_url

    context = {
        'site_title': _(ADMIN_SITE_HEADER),
        'title': _("Order Summary"),
        'ref_url': referer
    }
    orderlines = DistributorOrderDetail.objects.filter(distributor_order_id=order_id,
                                                       item_status__in=[OrderStatus.ORDERED]).select_related(
        'distributor_order__distributor', 'distributor_order',
        'shipping_address', 'product', 'distributor_order__shakti_enterpreneur')

    if request.POST.get('dispatch_order_submit'):
        from django.contrib import messages
        order = DistributorOrder.objects.filter(pk=order_id).first()
        context.update({
            'order': order, })
        # if (dt.now() - order.created).days > DISPATCH_DAYS:
        #     messages.error(
        #         request, 'Can not dispatch order older than 15 days.')
        #     return HttpResponseRedirect(request.build_absolute_uri())

        orderlines = DistributorOrderDetail.objects.filter(distributor_order_id=order_id).\
            select_related('distributor_order__distributor', 'distributor_order',
                           'shipping_address', 'product', 'distributor_order__shakti_enterpreneur')

        dispatch_keys = [key for key in request.POST.keys(
        ) if key.startswith("dispatch_quantity")]
        order_amount = total_amount = discount_amount = total_tax = 0
        promotions = []

        for dispatch_key in dispatch_keys:
            detail_id = dispatch_key.split('-')[1]
            orderline = DistributorOrderDetail.objects.filter(
                pk=detail_id).first()
            promo_key = 'applied_promos-{0}'.format(detail_id)
            promotion_id = request.POST.get(promo_key)

            promo_name_key = 'applied_promos_name-{0}'.format(detail_id)
            promotion_applied = request.POST.get(promo_name_key, '')

            if not promotion_id or promotion_id == '0':
                promotion = []
                promotion_obj = None
            else:
                promotion = [promotion_id]
                try:
                    promotion_obj = PromotionLines.objects.get(id=promotion_id)
                except:
                    print(promotion_id)
                    promotion_obj = PromotionLines.objects.filter(
                        id=int(promotion_id)).first()
                promotions.append(promotion_id)
            orderline.promotion = promotion
            orderline.promotion_applied = promotion_applied

            disc_key = 'applied_discount-{0}'.format(detail_id)
            discount = float(request.POST.get(disc_key, 0.0))

            dis_disc_key = 'applied_dis_discount-{0}'.format(detail_id)
            dis_discount = float(request.POST.get(dis_disc_key, 0.0))

            dispatch_quantity = int(request.POST.get(dispatch_key, 0))
            if dispatch_quantity < 0:
                messages.error(
                    request, 'Please enter correct dispatch quantity.')
                return HttpResponseRedirect(request.build_absolute_uri())

            orderline.dispatch_quantity = dispatch_quantity
            orderline.discount_amount = discount

            distributor_order_obj = DispatchDistributorOrder()

            orderline = distributor_order_obj.calculate_orderline_amount(
                orderline, promotion_obj)

            total_tax += orderline.cgst + orderline.sgst + orderline.igst
            total_amount += orderline.net_amount
            order_amount += orderline.price
            discount_amount += orderline.discount_amount
            discount_amount += orderline.distributor_discount

            orderline.item_status = OrderStatus.DISPATCHED
            # orderline.distributor_discount = dis_discount
            orderline.save()

        order_obj = DistributorOrder.objects.get(pk=order_id)
        order_obj.order_status = OrderStatus.DISPATCHED

        order_obj.total_amount = total_amount
        order_obj.tax = total_tax
        order_obj.amount = order_amount
        order_obj.discount_amount = discount_amount
        order_obj.promotion = promotions
        order_obj.save()

        messages.success(request, 'Order %s has been dispatched.' %
                         orderlines[0].distributor_order.invoice_number)

        return HttpResponseRedirect(redirect_url)

    if orderlines:
        order = orderlines[0].distributor_order
        distributoroffers = {}

        if hasattr(order.distributor.regionaldistributor, 'disitrbutoroffers'):
            distributoroffers_set = order.distributor.regionaldistributor.distributoroffers
            distributoroffers = {'id': distributoroffers_set.id,
                                 'discount': distributoroffers_set.discount,
                                 }

        orderlines, promotions = OrderManagement.add_available_stock(
            orderlines, order.distributor_id, order.shakti_enterpreneur_id)
        shakti = ShaktiEntrepreneur.objects.values(
            'code').get(user=order.shakti_enterpreneur)

        context.update({
            'order': order,
            'orderlines': orderlines,
            'shakti_code': shakti['code'],
            'promotions': promotions,
            'distributoroffers': distributoroffers,
            'distributor_products': DistributorStock.objects.filter(
                distributor=order.distributor).filter(created__gte=dt.now().date())
        })
    return TemplateResponse(request, 'admin/orders/dispatch_stockist_order.html',
                            context)


@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def add_product_secondary_order(request):
    data = json.loads(request.body)
    product = Product.objects.get(id=data["product_id"])
    order = DistributorOrder.objects.get(id=data["order_id"])
    dis_percentage = order.distributor.regionaldistributor.distributoroffers.discount
    base_rate = product.base_rate
    product_info = json.dumps(
        Product.objects.values('partner_code', 'brand_id',
                               'basepack_code', 'cgst', 'sgst',
                               'igst', 'basepack_name', 'base_rate',
                                       'cld_configurations', 'brand__stockist_margin',
                                       'category_id', 'mrp').get(id=data["product_id"]))

    order_details = DistributorOrderDetail.objects.create(
        distributor_order=order,
        product=product,
        quantity=0,
        unitprice=round(
            base_rate + (base_rate * product.brand.stockist_margin / 100), 5),
        price=0,
        igst=0,
        sgst=0,
        cgst=0,
        net_amount=0,
        discount_amount=0,
        distributor_discount_percent=dis_percentage,
        product_info=product_info,
        promotion=[]
    )

    print(order)
    print(order_details)

    return JsonResponse(data)
