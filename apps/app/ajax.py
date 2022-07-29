''' app/ajax.py will contain functions called from ajax '''
import json
from django.http import HttpResponse
from app.models import AlliancePartner

def get_partner_code(request):
    ''' to get code of selected alliance '''
    alliancecode = None
    if request.method == 'GET':
        allianceid = request.GET['allianceid']
        if allianceid is not None:
            alliancecode = AlliancePartner.objects.values('code').filter(pk=allianceid).first()

    result = json.dumps(alliancecode)
    return HttpResponse(result, content_type='applicaiton/json')
