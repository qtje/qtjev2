import django.db.models
from django import forms
from django.core.exceptions import ValidationError

from . import models

"""
I think I need some sort of customized ModelChoiceField that uses AutocompleteWidget
and also handles constructing querysets from historied models. Then I can also better
control construction of the widget as well.
Ultimately I think I need a custom Form class as well, and possible a custom view class.
I need the form to know the user, I need the view to check that the user is allowed to edit this thing
"""

class AutocompleteWidget(forms.TextInput):
    template_name = "comic/autocomplete_widget.html"

    def __init__(self, choices, attrs=None):
        super().__init__(attrs)
        self.choices = choices

    def get_context(self, name, value, attrs):
        list_name = attrs.get('list', None)
        if list_name is None:
            attrs['list'] = f'list_{name}'

        choices = self.choices
        choices = [(x.search_key(), x.search_string()) for x in choices]

        context = super().get_context(name, value, attrs)
        context['widget']['datalist'] = choices# [x[0].search_string() for x in self.choices]

        context['widget']['id'] = attrs['list']
        return context

    def render(self, name, value, attrs=None, renderer=None):
        result = super().render(name, value, attrs, renderer)
        return result

class HistoryModelField(forms.Field):
    widget=AutocompleteWidget
    def __init__(self, model, choices, **kwargs):
        kwargs['widget'] = self.widget(choices = choices)
        self.model = model
        super().__init__(**kwargs)

    def clean(self, value):
        hk = self.model.get_hk(value)
        if hk is not None:
            try:
                instance = self.model.get_latest(hk)
            except ValueError:
                raise ValidationError(f"Malformed key '{hk}'")
            except (self.model.DoesNotExist, ValueError):
                raise ValidationError(f"Couldn't find entity '{value}' with key '{hk}'")
        else:
            return None
        return instance


class PageEditForm(forms.ModelForm):

    is_create = False

    def add_history_field(self, name, user, model, instance, choices = None, **kwargs):
        if choices is None:
            choices = model.get_all_latest(user=user)
        self.fields[name] = HistoryModelField(model=model, choices=choices, **kwargs)
        if not instance is None:
            self.initial[name] = instance.search_key()

    def __init__(self, **kwargs):
        self.request = kwargs.pop('request')
        instance = kwargs['instance']

        print(kwargs)
        result = super().__init__(**kwargs)

        user = self.request.user
        self.add_history_field('template', None, models.PageTemplate, instance.template)
        self.add_history_field('theme', None, models.PageTheme, instance.theme)
        self.add_history_field('arc', None, models.ComicArc, instance.arc)
        self.add_history_field('owner', user, models.Alias, instance.owner)


        return result

    def is_valid(self):
        
        self.add_error(None, 'Nope')
        return super().is_valid()

    class Meta:
        model = models.ComicPage
        exclude = ['hk', 'template', 'theme', 'arc', 'owner']
        widgets = {
            'page_key': forms.HiddenInput,
            'title': forms.TextInput,
            'alt_text': forms.TextInput,
        }
#        fields = ['title', 'arc', 'image', 'alt_text']

class PageCreateForm(PageEditForm):
    reciprocate_owner = forms.BooleanField(initial = True)   
    is_create = True

    def __init__(self, **kwargs):
        result = super().__init__(**kwargs)

        self.add_history_field('prev_page_owner', None, models.ComicPage, None, required=False)

        return result

    def is_valid(self):
        prev_page_raw = self.data['prev_page_owner']
        if prev_page_raw is not None:
            try:
                prev_page = self.fields['prev_page_owner'].clean(prev_page_raw)
            except:
                pass #This error will get caught later
            else:
                if not prev_page.can_link('n', self.request.user):
                    self.add_error('reciprocate_owner', f'The page {prev_page.search_key()} already has too many next links.')

        return super().is_valid()



