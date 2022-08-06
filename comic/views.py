from django.shortcuts import render

from django.http import HttpResponse

from django.views import generic



from .models import ComicPage, ForumPost

# Create your views here.

class ComicView(generic.DetailView):
    model = ComicPage 
    template_name = 'comic/main.html'

    def get_object(self, queryset = None):
        result =  ComicPage.objects.get(page_key=self.kwargs.get('pk', '0000'))
        return result

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
