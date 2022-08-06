
import datetime

from django.db import models
from django.db.models import signals as model_signals
from django.conf import settings

from django.contrib.auth.models import User

from django.template import Template, Context

# Create your models here.

"""
I would like to make the django admin be able to show only the latest versions
of Historied models.

Need a set of pages for authors to use to make changes. I think I just need to take complete control over the forms available to authors rather than using the admin site. This way I can more clearly define the actions and author can take and create UX that's tailored to making those actions managable.
This will be mainly a set of listviews that also include an Add button at the top
Paired with a set of detailviews, I suppose? or some kind of form view

Need to work out how to have author accounts
That stuff is all in https://docs.djangoproject.com/en/4.0/topics/auth/default/#module-django.contrib.auth.views

Need to implement authors and forum views

Need to implement rss feeds
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


    def as_of(self, date):
        result =  self.__class__.objects.filter(
                    hk = self.hk).order_by(
                    '-created_at').filter(created_at__lte=date)[0]
        return result

    @staticmethod
    def filter_owner(queryset, user):
        return queryset.filter(owner__owner__user=user)

    @classmethod
    def get_all_latest(cls, user, key='kh'):
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



class Alias(OwnedHistory):
    display_name = models.TextField()
    owner = models.ForeignKey(Author, on_delete = models.CASCADE, related_name = 'aliases')

    def is_conflicted(self):
        count = Alias.objects.filter(display_name=self.display_name).count()
        return count > 1

    @staticmethod
    def filter_owner(queryset, user):
        return queryset.filter(owner__user=user)

    def __str__(self):
        return f'{self.display_name} ({self.owner})'


### Comic Customization ###

class PageTemplate(OwnedHistory):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_templates')
    name = models.TextField()
    template = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.name} ({self.owner}) as of {self.created_at}'

class PageTheme(OwnedHistory):
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

### Comic Structure ###

class ComicArc(OwnedHistory):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_arcs')
    slug_name = models.TextField()
    display_name = models.TextField()

    def __str__(self):
        return f'{self.display_name} ({self.slug_name}) - {self.owner}'


class ComicPage(OwnedHistory):
    """
    The contents of a page at a point in time.
    """
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_pages')

    page_key = models.TextField() #4 hex digits

    title = models.TextField()
    arc = models.ForeignKey(ComicArc, on_delete = models.CASCADE)

    image = models.ImageField(upload_to='images')
    alt_text = models.TextField()

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

    def __str__(self):
        self.old_from = self.links_from.all()
        self.old_to = self.links_to.all()

        return f'Page {self.page_key} as of {self.created_at}'

def page_post_save(**kwargs):
    """
    When a new History instance is created, and the hk hasn't been set
    (it should not be set manually), the hk will be updated to match the pk
    """
    instance = kwargs['instance']
    
    if isinstance(instance, ComicPage):
        for entry in instance._old_from:
            if entry.deleted_at is None:
                entry.from_page = instance
                entry.save()
        for entry in instance._old_to:
            if entry.deleted_at is None:
                entry.to_page = instance
                entry.save()

model_signals.post_save.connect(page_post_save)



class ComicLink(models.Model):
    """
    The contents of a page link at a point in time
    """
    created_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_links')
    LINK_KINDS = (
        ('n', 'next'),
        ('p', 'prev'),
        ('f', 'first'),
        ('d', 'deleted'),
        )

    from_page = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'links_from')
    to_page = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'links_to')
    kind = models.TextField(choices=LINK_KINDS)

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

