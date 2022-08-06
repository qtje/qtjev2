import datetime

import django.db.models
import django.template
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

    def get_instance(self, value):
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

    def clean(self, value):
        return self.get_instance(value)

class MyForm(forms.ModelForm):

    template_name = 'comic/author_form.html'
    is_create = False

    def __init__(self, **kwargs):
        self.request = kwargs.pop('request')
        instance = kwargs['instance']
        if instance is not None:
            self.target = kwargs['instance'].get_hk_value()
        return super().__init__(**kwargs)

    def add_history_field(self, name, user, model, instance, choices = None, **kwargs):
        if choices is None:
            choices = model.get_all_latest(user=user)
        self.fields[name] = HistoryModelField(model=model, choices=choices, **kwargs)
        if instance == 'auto':
            instance = choices[-1]
        if not instance is None:
            self.initial[name] = instance.search_key()

    def add_owner_field(self, user, instance):
        default = 'auto'
        if instance is not None:
            default = instance.owner
        self.add_history_field('owner', user, models.Alias, default)
        self.order_fields(['owner'])

    def get_page_from_field(self, field_name):
        raw = self.data[field_name]
        try:
            result = self.fields[field_name].get_instance(raw)
        except:
            return None
        return result

    def get_owner(self):
        return self.cleaned_data['owner']

    def save(self, commit=True):
        if self.is_create:
            self.instance.hk = self.Meta.model.get_next_hk()
            owner = self.get_owner()
            self.instance.owner_id = owner.id

        instance = super().save(commit)

        return instance




class PageEditForm(MyForm):

    def __init__(self, **kwargs):
        result = super().__init__(**kwargs)

        instance = kwargs['instance']

        user = self.request.user
        defaults = {}
        if instance is not None:
            defaults = {
            'template': instance.template,
            'theme': instance.theme,
            'arc': instance.arc,
            'owner': instance.owner
            }

        self.add_history_field('template', None, models.PageTemplate, defaults.get('template','auto'))
        self.add_history_field('theme', None, models.PageTheme, defaults.get('theme', 'auto'))
        self.add_history_field('arc', None, models.ComicArc, defaults.get('arc', 'auto'))
        self.add_owner_field(user, instance)

        return result

    def is_valid(self):
        if not self.fields['owner'].get_instance(self.data['owner']).is_owned_by(self.request.user):
            self.add_error('owner', 'Please enter an alias that you own.')
        return super().is_valid()

    def save(self, commit=True):
        self.instance.arc_id = self.cleaned_data['arc'].id
        self.instance.owner_id = self.cleaned_data['owner'].id
        self.instance.template_id = self.cleaned_data['template'].id
        self.instance.theme_id = self.cleaned_data['theme'].id

        return forms.ModelForm.save(self, commit)

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
    reciprocate_owner = forms.BooleanField(initial = True, required=False)   
    is_create = True

    def __init__(self, **kwargs):
        
        result = super().__init__(**kwargs)
        self.initial['page_key'] = models.ComicPage.get_next_page_key()
        self.add_history_field('prev_page_owner', None, models.ComicPage, None, required=False)

        return result

    def is_valid(self):
        self.prev_page = None

        self.prev_page = prev_page = self.get_page_from_field('prev_page_owner')

        if self.data.get('reciprocate_owner', False):
            if prev_page is not None:
                if not prev_page.can_link('n', self.request.user):
                    self.add_error('reciprocate_owner', f'{prev_page.search_string()} already has too many next links.')
            else:
                self.add_error('prev_page_owner', "If you really don't want to link to a previous page, uncheck reciprocate")

        return super().is_valid()

    def save(self, commit=True):
        owner = self.cleaned_data['owner']

        instance = super().save(commit)

        if not commit: return instance

        if self.prev_page is not None:
            link = models.ComicLink(kind='p', 
                    from_page_id = instance.id, 
                    to_page_id = self.prev_page.id, 
                    owner=owner)
            link.save()
            if self.cleaned_data['reciprocate_owner']:
                link = models.ComicLink(kind='n', 
                        to_page_id = instance.id, 
                        from_page_id = self.prev_page.id, 
                        owner=owner)
                link.save()

        return instance



#
# Link create
#

class LinkCreateForm(MyForm):

    is_create = True
    post_url = 'comic:edit_link'

    button = 'Create Link'
    heading = 'Creating new link'

    reciprocate = forms.BooleanField(initial = True, required=False)   
    kind = forms.ChoiceField(choices = [('n', 'Next'), ('p', 'Previous')]) 

    def __init__(self, **kwargs):
        instance = kwargs['instance']
        result = super().__init__(**kwargs)

        user = self.request.user
        self.add_owner_field(user, instance)
        self.add_history_field('from_page', None, models.ComicPage, None, required=False)
        self.add_history_field('to_page', None, models.ComicPage, None, required=False)


        return result

    def is_valid(self):

        self.from_page = from_page = self.get_page_from_field('from_page')
        self.to_page = to_page = self.get_page_from_field('to_page')

        kind = self.data['kind']

        error_string = '{} already has too many links of the selected kind.'

        if from_page is not None and not from_page.can_link(kind, self.request.user):
            self.add_error('from_page', error_string.format(from_page.search_string()))

        if self.data.get('reciprocate', False):
            self.rec_kind = rec_kind = {'n':'p', 'p':'n'}[kind]
            if to_page is not None and not to_page.can_link(rec_kind, self.request.user):
                self.add_error('to_page', error_string.format(to_page.search_string()))
                self.add_error('reciprocate', error_string.format(to_page.search_string()))

        return super().is_valid()


    def save(self, commit=True):
        owner = self.cleaned_data['owner']

        instance = forms.ModelForm.save(self, commit)

        if not commit: return instance

        if self.cleaned_data.get('reciprocate', False):
            link = models.ComicLink(kind=self.rec_kind,
                    from_page_id = self.to_page.id, 
                    to_page_id = self.from_page.id, 
                    owner=owner)
            link.save()

        return instance



    class Meta:
        model = models.ComicLink
        exclude = ['hk', 'deleted_at']
        widgets = {
        }



#
# Arc edit
#

class ArcEditForm(MyForm):

    is_create = False
    post_url = 'comic:edit_arc'

    button = 'Update Story Arc'

    def __init__(self, **kwargs):
        instance = kwargs['instance']
        if not self.is_create:
            self.heading = f'Editing story arc {instance.display_name} {(instance.slug_name)}'
        result = super().__init__(**kwargs)
        self.add_owner_field(self.request.user, instance)
        return result


    class Meta:
        model = models.ComicArc
        exclude = ['hk']
        widgets = {
            'slug_name': forms.TextInput,
            'display_name': forms.TextInput
        }

class ArcCreateForm(ArcEditForm):

    is_create = True
    post_url = 'comic:edit_arc'

    heading = 'Creating new story arc'
    button = 'Create Story Arc'


#
# Alias edit
#

class AliasEditForm(MyForm):

    is_create = False
    post_url = 'comic:edit_alias'

    button = 'Update Alias'

    def __init__(self, **kwargs):
        instance = kwargs['instance']
        if not self.is_create:
            self.heading = f'Editing alias {instance.display_name}'
        return super().__init__(**kwargs)

    def get_owner(self):
        return models.Author.objects.get(user=self.request.user)

    class Meta:
        model = models.Alias
        exclude = ['hk', 'owner']
        widgets = {
            'display_name': forms.TextInput
        }

class AliasCreateForm(AliasEditForm):

    is_create = True
    post_url = 'comic:edit_alias'

    heading = 'Creating new alias'
    button = 'Create Alias'

#
# Template edit
#

class TemplateEditForm(MyForm):

    is_create = False
    post_url = 'comic:edit_template'

    button = 'Update Template'

    field_order = ['owner', 'name', 'template']

    def __init__(self, **kwargs):
        instance = kwargs['instance']
        if not self.is_create:
            self.heading = f'Editing template {instance.name}'
        result = super().__init__(**kwargs)
        self.add_owner_field(self.request.user, instance)
        return result

    def is_valid(self):
        template = self.data['template']

        if template is not None and template != '':
            try:
                date = datetime.datetime.now(datetime.timezone.utc)
                test_data = models.ComicPage.get_test_page()
                test_data.render_template(date, template_text=template)
            except Exception as e:
                self.add_error('template', str(e))

        return super().is_valid()

    class Meta:
        model = models.PageTemplate
        exclude = ['hk', 'owner']
        widgets = {
            'name': forms.TextInput
        }

class TemplateCreateForm(TemplateEditForm):

    is_create = True
    post_url = 'comic:edit_template'

    heading = 'Creating new template'
    button = 'Create Template'


#
# Theme edit
#

class ThemeEditForm(MyForm):

    is_create = False
    post_url = 'comic:edit_theme'

    button = 'Update Theme'

    def __init__(self, **kwargs):
        instance = kwargs['instance']
        if not self.is_create:
            self.heading = f'Editing theme {instance.name}'
        result = super().__init__(**kwargs)
        self.add_owner_field(self.request.user, instance)
        return result

    def is_valid(self):


        date = datetime.datetime.now(datetime.timezone.utc)
        try:
            test_data = models.ComicPage.get_test_page()
        except:
            test_data = None

        if test_data is not None:
            for key in models.PageTheme.keys:
                try:
                    template_text = self.data[key]
                    if template_text is None or template_text == '':
                        continue
                    test_data.render_theme(date, {key:django.template.Template(template_text)} )

                except Exception as e:
                    self.add_error(key, str(e))

        return super().is_valid()

    class Meta:
        model = models.PageTheme
        exclude = ['hk', 'owner']
        widgets = {
            'name': forms.TextInput
        }

class ThemeCreateForm(ThemeEditForm):

    is_create = True
    post_url = 'comic:edit_theme'

    heading = 'Creating new theme'
    button = 'Create Theme'






