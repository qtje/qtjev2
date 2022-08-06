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

        date = self.request.GET.get('date', None)
        if date is None:
            date = datetime.datetime.utcnow()
        else:
            date = dateutil.parser.parse(date)

        try:
            result =  models.ComicPage.objects.filter(
                        page_key=self.kwargs.get('pk', '0000')).order_by(
                        '-created_at').filter(created_at__lte=date)[0]
        except IndexError:
            return None
                    
        if result is not None:

            result.querystring = self.request.GET.urlencode()

            links_from = result.links_from.exclude(deleted_at__lte=date).exclude(created_at__gt=date)

            result.next_links = links_from.filter(kind='n')
            result.prev_links = links_from.filter(kind='p')
            result.first_links = links_from.filter(kind='f')

            result.arc = result.arc.as_of(date)

            template = Template(result.template.as_of(date).template)
            theme = result.theme.as_of(date)   
 
            body = template.render(Context({'object': result}))

            result.body = body
            return result

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
