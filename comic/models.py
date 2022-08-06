
import datetime

from django.db import models
from django.conf import settings

from django.contrib.auth.models import User

import simple_history
from simple_history.models import HistoricalRecords

# Create your models here.

### Authors ###

class Author(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete = models.CASCADE)

    def __str__(self):
        return f'{self.user}'

class Alias(models.Model):
    display_name = models.TextField()
    owner = models.ForeignKey(Author, on_delete = models.CASCADE, related_name = 'aliases')
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.display_name} ({self.owner})'



class OwnedHistory(models.Model):
    owner = models.ForeignKey(Alias, on_delete = models.CASCADE)   

### Comic Customization ###

class PageTemplate(OwnedHistory):
    name = models.TextField()
    template = models.TextField()

    def __str__(self):
        return f'{self.name} ({self.owner})'

simple_history.register(PageTemplate)

class PageTheme(OwnedHistory):
    name = models.TextField()

    def __str__(self):
        return f'{self.name} ({self.owner})'

simple_history.register(PageTheme)

### Comic Structure ###

class ComicArc(OwnedHistory):
    slug_name = models.TextField()
    display_name = models.TextField()

    def __str__(self):
        return f'{self.display_name} ({self.slug_name}) - {self.owner}'

simple_history.register(ComicArc)


class ComicPage(OwnedHistory):
    """
    The contents of a page at a point in time.
    """

    page_key = models.TextField() #4 hex digits

    title = models.TextField()
    arc = models.ForeignKey(ComicArc, on_delete = models.CASCADE)

    image = models.ImageField()
    alt_text = models.TextField()

    template = models.ForeignKey(PageTemplate, on_delete = models.CASCADE)

    theme = models.ForeignKey(PageTheme, on_delete = models.CASCADE)

    def __str__(self):
        return f'Page {self.page_key}'

simple_history.register(ComicPage)

class ComicLink(OwnedHistory):
    """
    The contents of a page link at a point in time
    """
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
    
simple_history.register(ComicLink)

### Forums ###

class ForumPost(models.Model):
    """
    A single forum post
    """
    text = models.TextField()
    timestamp = models.DateTimeField()
    source = models.ForeignKey(ComicPage, on_delete = models.CASCADE, related_name = 'forum_posts')

