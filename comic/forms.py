from django import forms

from . import models

"""
I think I need some sort of customized ModelChoiceField that uses AutocompleteWidget
and also handles constructing querysets from historied models. Then I can also better
control construction of the widget as well.
Ultimately I think I need a custom Form class as well, and possible a custom view class.
I need the form to know the user, I need the view to check that the user is allowed to edit this thing
"""

class DummyWidget(forms.Widget):
        template_name = "comic/dummy_widget.html"

class AutocompleteWidget(forms.TextInput):
    template_name = "comic/autocomplete_widget.html"

    def __init__(self, choices, model, user, attrs=None):
        super().__init__(attrs)
        self.choices = choices
        self.model = model
        self.user = user

    def get_context(self, name, value, attrs):
        list_name = attrs.get('list', None)
        if list_name is None:
            attrs['list'] = f'list_{name}'

        choices = self.choices(user=self.user)
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
    def __init__(self, user, model, **kwargs):
        self.model = model
        self.user = user
        choices = model.get_all_latest
        kwargs['widget'] = self.widget(choices = choices, model=model, user=user)
        super().__init__(**kwargs)
        


class PageEditForm(forms.ModelForm):

#    next_page_owner = HistoryModelField(
#        model=models.ComicPage
#        )
#    next_page_any = HistoryModelField(model=models.ComicPage)

    reciprocate_owner = forms.BooleanField()
    reciprocate_any = forms.BooleanField()

    def add_history_field(self, name, user, model, instance):
        self.fields[name] = HistoryModelField(model=model, user=user)
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

        self.add_history_field('next_page_owner', None, models.ComicPage, None)
        self.add_history_field('next_page_any', None, models.ComicPage, None)


        return result


    class Meta:
        model = models.ComicPage
        exclude = ['hk', 'template', 'theme', 'arc', 'owner']
        widgets = {
            'page_key': DummyWidget,
            'title': forms.TextInput,
            'alt_text': forms.TextInput,
        }
#        fields = ['title', 'arc', 'image', 'alt_text']

