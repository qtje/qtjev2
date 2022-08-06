from django.urls import path

from django.contrib.auth import views as auth_views

from . import views

app_name = 'comic'

urlpatterns = [
    path('authors', views.AuthorsView.as_view(), name='authors'),
    path('forum', views.index, name='forum'),
    path('archive', views.index, name='archive'),
    path('post', views.do_forum_post),

    path('login', auth_views.LoginView.as_view(template_name='comic/author_login.html', next_page='comic:index'), name='login'),

    path('edit/page/<str:pk>', views.PageEditView.as_view(), name='edit_page'),
    path('edit/page', views.PageCreateView.as_view(), name='create_page'),


    path('edit/arc/<int:hk>', views.ArcEditView.as_view(), name='edit_arc'),
    path('edit/arc', views.ArcCreateView.as_view(), name='edit_arc'),
    path('edit/link', views.LinkCreateView.as_view(), name='edit_link'),

    path('edit/alias/<int:hk>', views.AliasEditView.as_view(), name='edit_alias'),
    path('edit/alias', views.AliasCreateView.as_view(), name='edit_alias'),
    path('edit/template/<int:hk>', views.TemplateEditView.as_view(), name='edit_template'),
    path('edit/template', views.TemplateCreateView.as_view(), name='edit_template'),
    path('edit/theme/<int:hk>', views.ThemeEditView.as_view(), name='edit_theme'),
    path('edit/theme', views.ThemeCreateView.as_view(), name='edit_theme'),


    path('list/pages', views.PageEditListView.as_view(), name='list_pages'),
    path('list/links', views.LinkEditListView.as_view(), name='list_links'),
    path('list/templates', views.TemplateEditListView.as_view(), name='list_templates'),
    path('list/themes', views.ThemeEditListView.as_view(), name='list_themes'),
    path('list/aliases', views.AliasEditListView.as_view(), name='list_aliases'),
    path('list/arcs', views.ArcEditListView.as_view(), name='list_arcs'),

    path('', views.ComicView.as_view(), name='index'),
    path('<str:pk>', views.ComicView.as_view(), name='page'),
]
