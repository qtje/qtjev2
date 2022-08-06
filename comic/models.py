
import datetime

from django.db import models
from django.db.models import signals as model_signals
from django.conf import settings

from django.contrib.auth.models import User

import simple_history
from simple_history.models import HistoricalRecords

# Create your models here.

"""
I would like to make the django admin be able to show only the latest versions
of Historied models.

I need to be able to hide created_at and hk fields in admin.

I need a way of automatically updating links to follow pages when they update
when a page saves, it should call save on all its attached links and point them
at itself, the new instance?
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
            print(f'An update was created')
            self.created_at = stamp
            self.pk = None
            self.id = None
            print(dir(self))
            kwargs['force_insert'] = True
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

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
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.display_name} ({self.owner})'



#class OwnedHistory(History):
#    owner = models.ForeignKey(Alias, on_delete = models.CASCADE)   

### Comic Customization ###

class PageTemplate(OwnedHistory):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_templates')
    name = models.TextField()
    template = models.TextField()

    def __str__(self):
        return f'{self.name} ({self.owner})'

class PageTheme(OwnedHistory):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE, related_name = 'owned_themes')
    name = models.TextField()

    def __str__(self):
        return f'{self.name} ({self.owner})'

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

    image = models.ImageField()
    alt_text = models.TextField()

    template = models.ForeignKey(PageTemplate, on_delete = models.CASCADE)

    theme = models.ForeignKey(PageTheme, on_delete = models.CASCADE)

    def __str__(self):
        return f'Page {self.page_key} as of {self.created_at}'

class ComicLink(OwnedHistory):
    """
    The contents of a page link at a point in time
    """
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
    timestamp = models.DateTimeField()
    source = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'forum_posts')

