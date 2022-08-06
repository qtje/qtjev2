import datetime
import dateutil.parser

from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

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
            date = datetime.datetime.now(datetime.timezone.utc)
        else:
            date = dateutil.parser.parse(date)

        try:
            pages =  models.ComicPage.objects.filter(
                        page_key=self.kwargs.get('pk', '0000')).order_by(
                        '-created_at').filter(created_at__lte=date)
            result = pages[0]
            result.first_version = pages.order_by('created_at')[0]
        except IndexError:
            return None
                    
        if result is not None:

            result.querystring = self.request.GET.urlencode()

            links_from = result.links_from.exclude(deleted_at__lte=date).exclude(created_at__gt=date)

            result.next_links = links_from.filter(kind='n')
            result.prev_links = links_from.filter(kind='p')
            result.first_links = links_from.filter(kind='f')

            forums = ForumPost.objects.order_by('-timestamp').exclude(timestamp__gt=date)
            forums_here = forums.filter(source__page_key = result.page_key)

            ref = None
            try:
                ref = forums[0]
                ref = forums_here[0]
            except IndexError:
                pass

            if ref is not None:
                forums = ForumPost.objects.order_by('-timestamp').exclude(timestamp__gt=ref.timestamp)
                result.forums = forums[:20]

            result.arc = result.arc.as_of(date)

            template = Template(result.template.as_of(date).template)
            theme = result.theme.as_of(date)   
 
            body = template.render(Context({'object': result}))

            result.body = body
            return result

forum_filter = str.maketrans({x: None for x in ',.:;\'"'})

def do_forum_post(request):
    if request.method != 'POST': return

    text = request.POST.get('comment', '')
    return_path = request.POST.get('return')
    source_key = request.POST.get('source')

    source = ComicPage.objects.filter(page_key=source_key)[0]

    text = text.lower()
    text = text.translate(forum_filter)

    post = models.ForumPost(text=text, source=source)
    
    post.save()

    return HttpResponseRedirect(return_path)

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
