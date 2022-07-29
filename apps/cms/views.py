'''CMS View'''
from django.shortcuts import render
from cms.models import CmsPage
# Create your views here.


def aboutus(request):
    '''About Us'''
    about = CmsPage.objects.filter(id=1).first()
    context = {'about': about}
    return render(request, 'cms/aboutus.html', context)
