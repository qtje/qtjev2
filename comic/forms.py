from django import forms

from . import models

class AutocompleteWidget(forms.TextInput):
    template_name = "comic/autocomplete_widget.html"

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs)
        # choices can be any iterable, but we may need to render this widget
        # multiple times. Thus, collapse it into a list so it can be consumed
        # more than once.
        self.choices = list(choices)

    def get_context(self, name, value, attrs):
        list_name = attrs.get('list', None)
        if list_name is None:
            attrs['list'] = f'list_{name}'

        context = super().get_context(name, value, attrs)
        self.choices = list(filter(lambda x: x[0] != '',self.choices))
        self.choices = [(x[0].instance.search_key(), x[0].instance.search_string()) for x in self.choices]
        context['widget']['datalist'] = self.choices# [x[0].search_string() for x in self.choices]

        context['widget']['id'] = attrs['list']
        return context

    def render(self, name, value, attrs=None, renderer=None):
        result = super().render(name, value, attrs, renderer)
        return result


class PageEditForm(forms.ModelForm):

    next_page_owner = forms.ModelChoiceField(
        queryset=models.ComicPage.objects, 
        widget=AutocompleteWidget
        )
    next_page_any = forms.ModelChoiceField(queryset=models.ComicPage.objects)

    class Meta:
        model = models.ComicPage
        exclude = ['hk', 'owner']
#        fields = ['title', 'arc', 'image', 'alt_text']

