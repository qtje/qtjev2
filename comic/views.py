import datetime
import dateutil.parser

from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from django.views import generic

from django.template import Template, Context

from django.contrib.auth.mixins import LoginRequiredMixin

import simple_history

from . import models
from .models import ComicPage, ForumPost

from . import forms

# Create your views here.

#
# Primary Page Views (For Users)
#

def process_date(date):
    """
    For handling optional dates passed by querystring
    Take a date string and turn it into a datetime object.
    If the date_str is None, return the current date instead.
    """
    if date is None:
        date = datetime.datetime.now(datetime.timezone.utc)
    else:
        date = dateutil.parser.parse(date)
    return date


def get_comic_page(date, page_key_str):
    """
    Retrieve a comic page by its page key and the target date.
    Enforce format of the page key
    """
    try:
        page_key = int(page_key_str, 16)
        page_key = f'{page_key:04}'
        pages =  models.ComicPage.objects.filter(
                    page_key=page_key).order_by(
                    '-created_at').filter(created_at__lte=date)
        result = pages[0]
        result.first_version = pages.order_by('created_at')[0]
    except IndexError:
        return None

    return result


class ComicView(generic.DetailView):
    model = ComicPage 
    template_name = 'comic/main.html'

    def get_object(self, queryset = None):

        date = self.request.GET.get('date', None)
        page_key_str = self.kwargs.get('pk', '0')

        date = process_date(date)
        result = get_comic_page(date, page_key_str)
 
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

            theme_context = Context({'object': result})

            template_text = result.template.as_of(date).template
            if template_text is not None and len(template_text) > 0:
                template = Template(template_text)
                result.body = template.render(theme_context)

            theme = result.theme.as_of(date)   
            theme_dict = theme.get_templates()
            result.theme_values = {k: v.render(theme_context) for k,v in theme_dict.items()}

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

#
# 
#

#
# Entity Create/Edit Views (For Authors)
#

class PageEditView(LoginRequiredMixin, generic.edit.UpdateView):
    login_url = '/login'

    model = ComicPage
    template_name = 'comic/page_edit.html'
    form_class = forms.PageCreateForm
 
    def get_object(self, queryset = None):

        page_key_str = self.kwargs.get('pk', '0')

        date = process_date(None)
        result = get_comic_page(date, page_key_str)

        return result

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result['request'] = self.request
        return result


    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
 

#
# Entity List Views (For Authors)
#

class EditListView(LoginRequiredMixin, generic.ListView):
    login_url = '/login'
    model = ComicPage
    template_name = 'comic/page_list.html'
    hk = 'hk'

    view_url = None
    edit_url = 'comic:page'
    new_url = 'comic:index'
    new_link_text = 'New Whatever'

    def get_queryset(self):
        return self.model.get_all_latest(self.request.user, self.hk)

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)

        result['table_map'] = self.render_table_map(result['object_list'])
        result['edit_url'] = self.edit_url
        result['new_url'] = self.new_url
        result['view_url'] = self.view_url
        result['new_link_text'] = self.new_link_text

        return result


class PageEditListView(EditListView):
    model = ComicPage
    hk = 'page_key'
    view_url = 'comic:page'
    edit_url = 'comic:edit_page'
    new_url = 'comic:index'
    new_link_text = 'New Page'

    def render_table_map(self, object_list):
        header = ['Page Number', 'Title', 'Story Arc', 'Alt Text', 'Owner', 'Last Modified']
        tables = []
        for entry in object_list:
            row_data = [entry.page_key, entry.title, entry.arc.display_name, entry.alt_text, entry.owner.display_name, entry.created_at]
            row = {
                'row_data': row_data,
                'edit_key': entry.page_key,
                'view_key': entry.page_key,
                }

            tables.append(row)

        return {
            'header': header,
            'rows' : tables,
        }

class LinkEditListView(EditListView):
    model = models.ComicLink
    edit_url = 'comic:page'
    new_url = 'comic:index'
    new_link_text = 'New Link'

    def render_table_map(self, object_list):
        header = ['Link type', 'From Page', 'To Page', 'Owner', 'Creation Date']
        tables = []
        for entry in object_list:
            row_data = [entry.kind, entry.from_page.page_key, entry.to_page.page_key, entry.owner.display_name, entry.created_at]
            row = {
                'row_data': row_data,
                'edit_key': entry.id,
                'view_key': entry.id,
                }

            tables.append(row)

        return {
            'header': header,
            'rows' : tables,
        }



class TemplateEditListView(EditListView):
    model = models.PageTemplate
    edit_url = 'comic:page'
    new_url = 'comic:index'
    new_link_text = 'New Template'

    def render_table_map(self, object_list):
        header = ['Key', 'Name', 'Owner', 'Last Modified']
        tables = []
        for entry in object_list:
            row_data = [entry.hk, entry.name, entry.owner.display_name, entry.created_at]
            row = {
                'row_data': row_data,
                'edit_key': entry.hk,
                'view_key': entry.hk,
                }

            tables.append(row)

        return {
            'header': header,
            'rows' : tables,
        }

class ThemeEditListView(EditListView):
    model = models.PageTheme
    edit_url = 'comic:page'
    new_url = 'comic:index'
    new_link_text = 'New Theme'

    def render_table_map(self, object_list):
        header = ['Key', 'Name', 'Owner', 'Last Modified']
        tables = []
        for entry in object_list:
            row_data = [entry.hk, entry.name, entry.owner.display_name, entry.created_at]
            row = {
                'row_data': row_data,
                'edit_key': entry.hk,
                'view_key': entry.hk,
                }

            tables.append(row)

        return {
            'header': header,
            'rows' : tables,
        }

class AliasEditListView(EditListView):
    model = models.Alias
    edit_url = 'comic:page'
    new_url = 'comic:index'
    new_link_text = 'New Alias'

    def render_table_map(self, object_list):
        header = ['Key', 'Name', 'Last Modified']
        tables = []
        for entry in object_list:
            row_data = [entry.hk, entry.display_name, entry.created_at]
            row = {
                'row_data': row_data,
                'edit_key': entry.hk,
                'view_key': entry.hk,
                }

            tables.append(row)

        return {
            'header': header,
            'rows' : tables,
        }



#
#
#
   
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
