
import datetime

from django.db import models
from django.db.models import signals as model_signals
from django.conf import settings

from django.contrib.auth.models import User

from django.template import Template, Context

from django.urls import reverse

import django.utils

# Create your models here.

"""
MVP:

Nice to have:
I need to audit owner alias management to make sure it's rendering dated versions properly and using hk's for direct comparisons rather than instances.

I need a story arcs listing page.<F6><F6>

It might be nice to have a memory of the user's last-used templates, arcs, etc to autopopulate the page creation form.

It's possible I should like make the Alias model have a user property that returns its owner's user in order to make ownership checking more consistent and less error-prone

"""


class OwnedHistory(models.Model):
    """
    When a History instance is updated, it instead creates a copy and updates
    the created_at date to the current date.

    This way, you can query a model relative to its created_at date to find the
    most recent version of an instance at any specified historical date.

    The history of an instance can be obtained by query for a historical key
    that doesn't have to be unique, but can't change in the process of updating
    an instance. This can be supplied by the subclass or it can be the hk that
    this class provides.

    An Integer field called hk is provided to serve as a universal historical key,
    but other fields may also be used as long as they don't change. For example
    a comic page index maybe be more convenient for querying than finding the hk
    associated with the comic page.
    """
    created_at = models.DateTimeField(auto_now=True)
    hk = models.IntegerField(null=True, blank=True)

    default_hk = 'hk'

    def save(self, *args, **kwargs):
        print(f'A history was saved: {self} {kwargs=}')
        stamp = datetime.datetime.utcnow()
        force_update = kwargs.get('force_update', False)
        if not force_update and self.pk is not None:

            self.created_at = stamp
            self.pk = None
            self.id = None
            kwargs['force_insert'] = True
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


    def as_of(self, date=None):
        result = self.__class__.objects.filter(hk = self.hk).order_by('-created_at')

        if date is not None:
            result =  result.filter(created_at__lte=date)
        return result[0]

    def is_owned_by(self, user):
        return self.owner.owner.user == user

    def get_hk_value(self):
        return getattr(self,self.default_hk)

    def sanitize(self, date):
        """
        Replaces anything that shouldn't get sent to a user template
        """
        self.author = self.owner.sanitize(date)
        self.owner = None
        return self

    @staticmethod
    def filter_owner(queryset, user):
        return queryset.filter(owner__owner__user=user)

    @classmethod
    def get_latest(cls, hk, key=None):
        if key is None:
            key = cls.default_hk
        result = cls.objects.filter(**{key: hk})
        result = result.order_by('-created_at')
        try:
            return result[0]
        except IndexError:
            raise cls.DoesNotExist()

    @classmethod
    def get_all_latest(cls, user=None, key=None):
        """
        user, if provided, filters results that are owned by user
        key, if specified, is the hk to use. Defaults to cls.default_hk
        """
        if key is None:
            key = cls.default_hk
        result = cls.objects
        if user is not None:
            result = cls.filter_owner(result, user)
        result = result.order_by(f'-{key}', '-created_at')
    
        res_map = {}
        for entry in result:
            keyval = getattr(entry,key)
            if not keyval in res_map.keys():
                res_map[keyval] = entry

        return list(res_map.values())

    @classmethod
    def get_next_hk(cls):
        latest = max(cls.objects.all(), key = lambda x: x.hk)
        return latest.hk+1
        
class Searchable():

    def search_string(self):
        return str(self)

    def search_index(self):
        return getattr(self, self.default_hk)

    def search_key(self):
        return f'{self.search_index()}: {self.search_string()}'

    @classmethod
    def get_hk(self, search_key):
        """
        Extract the hk value from the given search_key
        """
        if search_key is None: return None
        if search_key == '': return None
        return search_key.split(':')[0]

def history_post_save(**kwargs):
    """
    When a new History instance is created, and the hk hasn't been set
    (it should not be set manually), the hk will be updated to match the pk
    """
    instance = kwargs['instance']
    
    if isinstance(instance, OwnedHistory):
        if instance.hk is None:
            instance.hk = instance.pk
            instance.save(force_update = True)

model_signals.post_save.connect(history_post_save)

class HistoryText(OwnedHistory):
    
    main = models.TextField()

### Authors ###

class Author(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)

    def __str__(self):
        return f'{self.user}'



class Alias(OwnedHistory, Searchable):
    display_name = models.TextField()
    owner = models.ForeignKey(Author, on_delete = models.CASCADE, related_name = 'aliases')

    conflict_icon = '⚠'
    warning = f'<span title="This name is used by multiple authors">{conflict_icon}</span>'

    def is_conflicted(self):
        count = Alias.objects.filter(display_name=self.display_name).count()
        return count > 1

    def is_owned_by(self, user):
        return self.owner.user == user

    def full_display_name(self):
        if not self.is_conflicted():
            return self.display_name
        else:
            return self.conflict_icon + ' ' + self.display_name


    def sanitize(self, date):
        """
        Returns a dictionary of values that can be used to safely render aliases
        in user-generated templates.
        """
        result = {}
        self = self.as_of(date)
        display_name_safe = django.utils.html.conditional_escape(self.display_name)
        if not self.is_conflicted():
            result['simple_name'] = display_name_safe
            result['html_name'] = display_name_safe
        else:
            result['simple_name'] = self.conflict_icon + ' ' + display_name_safe
            result['html_name'] = self.warning + ' ' + display_name_safe
        return result


    @staticmethod
    def filter_owner(queryset, user):
        return queryset.filter(owner__user=user)

    def __str__(self):
        return f'{self.display_name} ({self.owner})'

    def search_string(self):
        self = self.as_of()
        return f'{self.display_name}'


### Comic Customization ###

class PageTemplate(OwnedHistory, Searchable):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_templates')
    name = models.TextField()
    template = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.owner}) as of {self.created_at}'

    def search_string(self):
        return f'{self.name} ({self.owner.search_string()})'

class PageTheme(OwnedHistory, Searchable):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_themes')
    name = models.TextField()

    extra_rss_links = models.TextField(null=True, blank=True)

    left_links = models.TextField(null=True, blank=True)
    center_links = models.TextField(null=True, blank=True)
    right_links = models.TextField(null=True, blank=True)

    nav_right = models.TextField(null=True, blank=True)

    meta_left = models.TextField(null=True, blank=True)
    meta_right= models.TextField(null=True, blank=True)

    keys = [
            'extra_rss_links', 'left_links', 'center_links', 'right_links', 'nav_right',
            'meta_left', 'meta_right',
            ]

    def get_templates(self):
        result = {}
        for key in self.keys:
            template = getattr(self, key)
            if template is None or len(template) == 0:
                continue
            result[key] = Template(template) 
        return result 

    def __str__(self):
        return f'{self.name} ({self.owner}) as of {self.created_at}'

    def search_string(self):
        return f'{self.name} ({self.owner.search_string()})'



### Comic Structure ###

class ComicArc(OwnedHistory, Searchable):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_arcs')
    slug_name = models.TextField()
    display_name = models.TextField()

    def __str__(self):
        return f'{self.display_name} ({self.slug_name}) - {self.owner}'

    def search_string(self):
        return f'{self.display_name} ({self.slug_name}) ({self.owner.search_string()})'

    class Meta:
        unique_together = ('slug_name', 'display_name')



class ComicPage(OwnedHistory, Searchable):
    """
    The contents of a page at a point in time.
    """
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_pages')

    page_key = models.TextField() #4 hex digits
    default_hk = 'page_key'

    title = models.TextField(blank = True, null = True)
    arc = models.ForeignKey(ComicArc, on_delete = models.CASCADE)

    image = models.ImageField(upload_to='images')
    alt_text = models.TextField(blank = True, null = True)

    transcript = models.TextField(blank=True, null=True)

    template = models.ForeignKey(PageTemplate, on_delete = models.CASCADE)

    theme = models.ForeignKey(PageTheme, on_delete = models.CASCADE)

    def save(self, *args, **kwargs):
        print(f'A Page history was saved: {self} {kwargs=}')
        stamp = datetime.datetime.utcnow()
        force_update = kwargs.get('force_update', False)
        if not force_update and self.pk is not None:
            self.created_at = stamp

            
            self._old_from = list(self.links_from.all())
            self._old_to = list(self.links_to.all())
 
            self.pk = None
            self.id = None
 
            kwargs['force_insert'] = True
            models.Model.save(self, *args, **kwargs)
        else:
            models.Model.save(self, *args, **kwargs)

    def can_link(self, kind, user):
        """
        Return True if the given user is allowed to add a from link of the
        given type to this page.
        kind is 'p' or 'n'.
        """
        assert kind in ['n', 'p']
        existing = self.links_from.filter(kind=kind).all()
        page_user = self.owner.owner.user
        total = len(existing)
        if page_user == user:
            existing = list(filter(lambda x: x.is_owned_by(user), existing))
        else:
            existing = list(filter(lambda x: not x.is_owned_by(page_user), existing))

        print(f'{existing=}')

        if len(existing) < 2 and total < 3: 
            return True

    def search_string(self):
        return f'Page {self.page_key}: {self.title} ({self.owner.search_string()})'

    def __str__(self):
        self.old_from = self.links_from.all()
        self.old_to = self.links_to.all()

        return f'Page {self.page_key} as of {self.created_at}'

    def get_absolute_url(self):
        return reverse('comic:page', kwargs={'pk': self.page_key})

    def render_template(self, date, template_text = None, context=None):
        if template_text is None:
            template_text = self.template.as_of(date).template

        if template_text is not None and len(template_text) > 0:
            if context is None:
                context = Context({'object': self})
            else:
                context= Context(context)
            template = Template(template_text)
            return template.render(context)

    def render_theme(self, date, theme_dict = None, context = None):

        if context is None:
            context = Context({'object': self})
        else:
            context= Context(context)

        if theme_dict is None:
            theme = self.theme.as_of(date)   
            theme_dict = theme.get_templates()

        theme_values = {k: v.render(context) for k,v in theme_dict.items()}

        return theme_values


    def sanitize(self, date):
        self.author = self.owner.sanitize(date)
        self.owner = None

        self.next_links = [x.sanitize(date) for x in self.next_links] 
        self.prev_links = [x.sanitize(date) for x in self.prev_links] 
        self.first_links = [x.sanitize(date) for x in self.first_links] 

        self.arc = self.arc.sanitize(date)

        self.template = self.template.sanitize(date)
        self.theme = self.theme.sanitize(date)

        return self

    @classmethod
    def get_view_page(cls, date, page_key_str, sanitize = True):
        """
        Retrieve a comic page by its page key and the target date.
        If the page exists, prepare it for rendering by a template
        """
        try:
            page_key = cls.clean_page_key(page_key_str)
            pages =  cls.objects.filter(
                        page_key=page_key).order_by(
                        '-created_at').filter(created_at__lte=date)
            result = pages[0]
            result.first_version = pages.order_by('created_at')[0]
        except ValueError:
            raise
        except IndexError:
            return None

        print(date)

        result.owner = result.owner.as_of(date)

        print(result.links_from.all())
        for entry in result.links_from.all():
            print(entry.deleted_at)
            print(entry.created_at)
        links_from = result.links_from.exclude(deleted_at__lte=date).exclude(created_at__gt=date)
        print(links_from)

        result.next_links = links_from.filter(kind='n')
        result.prev_links = links_from.filter(kind='p')
        result.first_links = links_from.filter(kind='f')

        def order_key(x):
            return [x.owner.hk != result.owner.hk, x.created_at]

        result.next_links = sorted(result.next_links, key = order_key)
        result.prev_links = sorted(result.prev_links, key = order_key, reverse=True)
        result.first_links = sorted(result.first_links, key = order_key)

        result.arc = result.arc.as_of(date)
    
        if sanitize:
            result = result.sanitize(date)
        return result

    @classmethod
    def get_test_page(cls):
        return cls.objects.all()[0]



    """
        if result is not None:

            theme_context = Context({'object': result})

            template_text = result.template.as_of(date).template
            if template_text is not None and len(template_text) > 0:
                template = Template(template_text)
                result.body = template.render(theme_context)

            theme = result.theme.as_of(date)   
            theme_dict = theme.get_templates()
            result.theme_values = {k: v.render(theme_context) for k,v in theme_dict.items()}

            return result
    """



    @classmethod
    def fmt_page_key(cls, page_key):
        return f'{page_key:04x}'

    @classmethod
    def clean_page_key(cls, page_key_str):
        page_key = int(page_key_str, 16)
        return cls.fmt_page_key(page_key)

    @classmethod
    def get_next_page_key(cls):
        keys = [int(x.page_key, 16) for x in cls.objects.all()]
        latest = max(keys)
        if latest >= 0xffff:
            raise RuntimeError('Out of keys')
        return cls.fmt_page_key(latest+1)


def page_post_save(**kwargs):
    """
    When a new History instance is created, and the hk hasn't been set
    (it should not be set manually), the hk will be updated to match the pk
    """
    instance = kwargs['instance']
    
    if isinstance(instance, ComicPage):
        try:
            for entry in instance._old_from:
                if entry.deleted_at is None:
                    entry.from_page = instance
                    entry.save()
        except AttributeError:
            pass #in the event there aren't any old from links
        try:
            for entry in instance._old_to:
                if entry.deleted_at is None:
                    entry.to_page = instance
                    entry.save()
        except AttributeError:
            pass

model_signals.post_save.connect(page_post_save)



class ComicLink(models.Model):
    """
    The contents of a page link at a point in time
    """
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_links')
    LINK_KINDS = {
        'n': 'Next',
        'p': 'Previous',
        'f': 'First',
        }

    from_page = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'links_from')
    to_page = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'links_to')
    kind = models.TextField(choices=LINK_KINDS.items())

    def kind_name(self):
        return self.LINK_KINDS[self.kind]

    def is_owned_by(self, user):
        return self.owner.owner.user == user

    @staticmethod
    def filter_owner(queryset, user):
        return queryset.filter(owner__owner__user=user)

    def sanitize(self, date):
        self.author = self.owner.sanitize(date)
        self.owner = None
        return self

    @classmethod
    def get_all_latest(cls, user, key=None):
        result = cls.objects
        result = result.filter(deleted_at__isnull=True)
        if user is not None:
            result = cls.filter_owner(result, user)
        result = result.order_by('-created_at')
   
        return result
     

    def __str__(self):
        return f'{self.kind} {self.from_page} to {self.to_page} ({self.owner})'
    
### Forums ###

class ForumPost(models.Model):
    """
    A single forum post
    """
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now = True)
    source = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'forum_posts')

    def empty(self):
        return self.text.strip() == '';

