import datetime
import dateutil.parser

from django.shortcuts import render

from django.http import HttpResponse

from django.views import generic

from django.template import Template, Context

import simple_history

from . import models
from .models import ComicPage, ForumPost

# Create your views here.

class ComicView(generic.DetailView):
    model = ComicPage 
    template_name = 'comic/main.html'

    def get_object(self, queryset = None):
        result =  models.ComicPage.objects.get(page_key=self.kwargs.get('pk', '0000'))

        date = self.request.GET.get('date', None)
        if date is None:
            date = datetime.datetime.utcnow()
        else:
            date = dateutil.parser.parse(date)

        template = Template(result.template.template)

        body = template.render(Context({'object': result}))

        result.body = body
        return result

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
