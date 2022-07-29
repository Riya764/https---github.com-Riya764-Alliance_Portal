'''app view'''
# -*- coding: utf-8 -*-

from celery_progress.views import get_progress
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.conf import settings
from django.shortcuts import render_to_response
from celery.result import AsyncResult
from django.http import Http404, HttpResponse
import os

def view_site(request):
    '''default index view'''
    return render_to_response('index.html', request)

class TaskStatus(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return get_progress(request, task_id=request.GET.get("task_id"))



def download_file_view(request):
    celery_result = AsyncResult(request.GET.get("task_id"))
    filename = os.path.join(settings.EXPORT_PATH,
                    "temp", celery_result.result)
    if os.path.exists(filename):
            fh = open(filename, 'rb')
            response = HttpResponse(
                fh.read(), content_type="application/ms-excel")
            outfile = os.path.basename(filename)
            response['Content-Disposition'] = "attachment; filename=%s" % outfile
            fh.close()
            os.remove(filename)
            return response
    raise Http404
