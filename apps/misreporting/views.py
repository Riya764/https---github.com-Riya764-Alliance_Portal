'''
mis reporting ajax functions
'''
import json
from django import forms
from django.shortcuts import render
from django.views.generic import View
from django.http.response import JsonResponse, HttpResponseRedirect
from app.models import (AlliancePartner, RegionalDistributor,
                        ShaktiEntrepreneur, RegionalSalesPromoter)


class DistributorByBrand(View):
    ''' get Distributor ids by brand '''

    def get(self, *args, **kwargs):
        try:
            brand = self.request.GET.get('brand', '0')
            queryset = RegionalDistributor.objects.values(
                'user_id').filter(alliance_partner__user_id=brand, is_active=True).order_by('user__name')
            data = {'success': False}
            data['distributors'] = [dis['user_id'] for dis in queryset]
            if len(data['distributors']) > 0:
                data['success'] = True
            if self.request.is_ajax():
                return JsonResponse(data)
            else:
                return HttpResponseRedirect('/admin')
        except Exception as e:
            message = '{0} id not provided'.format('Brand')
            status_code = 200
            return JsonResponse({'message': message}, status=status_code)


class RspByDistributor(View):
    ''' get rsp ids by distributor '''

    def get(self, *args, **kwargs):
        try:
            data = self.request.GET.get('distributor')
            rs_ids = json.loads(data) if bool(data) else []
            queryset = RegionalSalesPromoter.objects.values(
                'user_id').filter(regional_distributor__user_id__in=rs_ids, is_active=True).order_by('user__name')
            data = {'success': False}
            data['rsps'] = [dis['user_id'] for dis in queryset]
            if len(data['rsps']) > 0:
                data['success'] = True
            if self.request.is_ajax():
                return JsonResponse(data)
            else:
                return HttpResponseRedirect('/admin')
        except Exception as e:
            message = '{0} id not provided'.format('rsp')
            status_code = 200
            return JsonResponse({'message': message}, status=status_code)


class ShaktiByRsp(View):
    ''' get shakti ids by rsp '''

    def get(self, *args, **kwargs):
        try:
            data = self.request.GET.get('rsp')
            rsp = json.loads(data) if bool(data) else []
            queryset = ShaktiEntrepreneur.objects.values(
                'user_id').filter(regional_sales__user_id__in=rsp, is_active=True).order_by('user__name')
            data = {'success': False}
            data['shaktis'] = [dis['user_id'] for dis in queryset]
            if len(data['shaktis']) > 0:
                data['success'] = True
            if self.request.is_ajax():
                return JsonResponse(data)
            else:
                return HttpResponseRedirect('/admin')
        except Exception as e:
            message = '{0} id not provided'.format('Shakti')
            status_code = 200
            return JsonResponse({'message': message}, status=status_code)


class RspByAlliance(View):
    '''Rsps by alliance '''

    def get(self, *args, **kwargs):
        try:
            alliance_partner = self.request.GET.get('alliance_partner', '0')
            queryset = RegionalSalesPromoter.objects.values(
                'user_id').filter(regional_distributor__alliance_partner__user_id=alliance_partner, is_active=True).order_by('user__name')
            data = {'success': False}
            data['rsps'] = [rsp['user_id'] for rsp in queryset]
            if len(data['rsps']) > 0:
                data['success'] = True
            if self.request.is_ajax():
                return JsonResponse(data)
            else:
                return HttpResponseRedirect('/admin')
        except Exception as e:
            message = '{0} id not provided'.format('Rsp')
            status_code = 200
            return JsonResponse({'message': message}, status=status_code)


class ShaktiByAlliance(View):
    '''Shakti by Alliance'''

    def get(self, *args, **kwargs):
        try:
            alliance_partner = self.request.GET.get('alliance_partner', '0')
            queryset = ShaktiEntrepreneur.objects.values(
                'user_id').filter(regional_sales__regional_distributor__alliance_partner__user_id=alliance_partner, is_active=True).order_by('user__name')
            data = {'success': False}
            data['ses'] = [se['user_id'] for se in queryset]
            if len(data['ses']) > 0:
                data['success'] = True
            if self.request.is_ajax():
                return JsonResponse(data)
            else:
                return HttpResponseRedirect('/admin')
        except Exception as e:
            message = '{0} id not provided'.format('Shakti')
            status_code = 200
            return JsonResponse({'message': message}, status=status_code)
