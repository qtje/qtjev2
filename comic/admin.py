from django.contrib import admin

from . import models

# Register your models here.

admin.site.register(models.Author)
admin.site.register(models.Alias)

admin.site.register(models.PageTemplate)
admin.site.register(models.PageTheme)

admin.site.register(models.ComicArc)

admin.site.register(models.ComicPage)

admin.site.register(models.ComicLink)

admin.site.register(models.ForumPost)
