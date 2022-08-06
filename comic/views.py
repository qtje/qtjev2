import datetime
import dateutil.parser

from django.shortcuts import render

from django.http import HttpResponse, HttpResponseRedirect

from django.views import generic

from django.template import Template, Context

from django.contrib.auth.mixins import LoginRequiredMixin

from django.urls import reverse_lazy

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

class ComicView(generic.DetailView):
    model = ComicPage 
    template_name = 'comic/main.html'

    def get_object(self, queryset = None):

        date = self.request.GET.get('date', None)
        page_key_str = self.kwargs.get('pk', '0')

        self.date = date = process_date(date)
        result = models.ComicPage.get_view_page(date, page_key_str)

        return result

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)

        instance = result['object']

        result['querystring'] = self.request.GET.urlencode()

        result['body'] = instance.render_template(self.date, context=result)
        result['theme_values'] = instance.render_theme(self.date, context=result)

        forums = ForumPost.objects.order_by('-timestamp').exclude(timestamp__gt=self.date)
        forums_here = forums.filter(source__page_key = instance.page_key)

        ref = None
        try:
            ref = forums[0]
            ref = forums_here[0]
        except IndexError:
            pass

        if ref is not None:
            forums = ForumPost.objects.order_by('-timestamp').exclude(timestamp__gt=ref.timestamp)
            forums = forums[:20]

        result['forums'] = forums

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
# Additional pages for users
#

class AuthorsView(generic.ListView):
    model = models.Alias

    def get_context_data(self, **kwargs):
        result = super().get_context_data(**kwargs)
        object_list = {}
        names_list = []
        for entry in result['object_list']:
            pages = models.ComicPage.objects.filter(owner = entry).order_by('-page_key')
            if not entry.display_name in object_list.keys():
                author_entry = {
                    'full_display_name': entry.full_display_name(),
                    }
                if len(pages) > 0:
                    author_entry['last'] = pages[0]
                    author_entry['first'] = pages[len(pages)-1]
                object_list[entry.display_name] = (author_entry)
            else:
                author_entry = object_list[entry.display_name]
                if len(pages) > 0:
                    if pages[0] > author_entry['last']:
                        author_entry['last'] = pages[0]
                    if pages[len(pages)-1] < author_entry['first']:
                        author_entry['first'] = pages[len(pages)-1]
                

        result['object_list'] = object_list.values()

        return result
        

#
# Entity Create/Edit Views (For Authors)
#

class PageEditView(LoginRequiredMixin, generic.edit.UpdateView):
    login_url = '/login'

    model = ComicPage
    template_name = 'comic/page_edit.html'
    form_class = forms.PageEditForm
 
    def get_object(self, queryset = None):

        page_key_str = self.kwargs.get('pk', '0')

        date = process_date(None)
        result = models.ComicPage.get_view_page(date, page_key_str)

        assert result.is_owned_by(self.request.user)

        return result

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result['request'] = self.request
        return result


    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class PageCreateView(LoginRequiredMixin, generic.edit.CreateView):
    login_url = '/login'

    model = ComicPage
    template_name = 'comic/page_edit.html'
    form_class = forms.PageCreateForm

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        if 'data' in result.keys():
            result['data'] = result['data'].copy()
            result['data']['page_key'] = models.ComicPage.get_next_page_key()
        result['request'] = self.request
        return result

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class GenericEditView(LoginRequiredMixin, generic.edit.UpdateView):
    login_url = '/login'

    template_name = 'comic/generic_edit.html'
 
    def get_object(self, queryset = None):
        result = self.model.get_latest(self.kwargs['hk'])
        #TODO: Make this more better
        assert result.is_owned_by(self.request.user)
        return result

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result['request'] = self.request
        return result

class GenericCreateView(LoginRequiredMixin, generic.edit.CreateView):
    login_url = '/login'
    success_url = reverse_lazy('comic:list_aliases')

    model = models.Alias
    template_name = 'comic/generic_edit.html'
    form_class = forms.AliasCreateForm

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result['request'] = self.request
        return result

class ArcEditView(GenericEditView):
    success_url = reverse_lazy('comic:list_arcs')
    model = models.ComicArc
    form_class = forms.ArcEditForm

class ArcCreateView(GenericCreateView):
    success_url = reverse_lazy('comic:list_arcs')
    model = models.ComicArc
    form_class = forms.ArcCreateForm



class AliasEditView(GenericEditView):
    success_url = reverse_lazy('comic:list_aliases')
    model = models.Alias
    form_class = forms.AliasEditForm

class AliasCreateView(GenericCreateView):
    success_url = reverse_lazy('comic:list_aliases')
    model = models.Alias
    form_class = forms.AliasCreateForm


class TemplateEditView(GenericEditView):
    success_url = reverse_lazy('comic:list_templates')
    model = models.PageTemplate
    form_class = forms.TemplateEditForm

class TemplateCreateView(GenericCreateView):
    success_url = reverse_lazy('comic:list_templates')
    model = models.PageTemplate
    form_class = forms.TemplateCreateForm

class ThemeEditView(GenericEditView):
    success_url = reverse_lazy('comic:list_themes')
    model = models.PageTheme
    form_class = forms.ThemeEditForm

class ThemeCreateView(GenericCreateView):
    success_url = reverse_lazy('comic:list_themes')
    model = models.PageTheme
    form_class = forms.ThemeCreateForm



#
# Entity List Views (For Authors)
#

class EditListView(LoginRequiredMixin, generic.ListView):
    login_url = '/login'
    model = ComicPage
    template_name = 'comic/page_list.html'
    hk = 'hk'

    view_url = None
    edit_url = 'comic:edit_page'
    new_url = 'comic:create_page'
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
    new_url = 'comic:create_page'
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
    edit_url = 'comic:edit_template'
    new_url = 'comic:edit_template'
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
    edit_url = 'comic:edit_theme'
    new_url = 'comic:edit_theme'
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
    edit_url = 'comic:edit_alias'
    new_url = 'comic:edit_alias'
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

class ArcEditListView(EditListView):
    model = models.ComicArc
    edit_url = 'comic:edit_arc'
    new_url = 'comic:edit_arc'
    new_link_text = 'New Story Arc'

    def render_table_map(self, object_list):
        header = ['Key', 'Slug', 'Name', 'Last Modified']
        tables = []
        for entry in object_list:
            row_data = [entry.hk, entry.slug_name, entry.display_name, entry.created_at]
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
