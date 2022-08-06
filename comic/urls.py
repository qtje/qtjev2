from django.urls import path

from django.contrib.auth import views as auth_views

from . import views

app_name = 'comic'

urlpatterns = [
    path('authors', views.index, name='authors'),
    path('forum', views.index, name='forum'),
    path('archive', views.index, name='archive'),
    path('post', views.do_forum_post),

    path('login', auth_views.LoginView.as_view(template_name='comic/author_login.html', next_page='comic:index'), name='login'),

    path('edit/page/<str:pk>', views.PageEditView.as_view(), name='edit_page'),
    path('edit/page', views.PageCreateView.as_view(), name='create_page'),

    path('edit/alias/<int:hk>', views.AliasEditView.as_view(), name='edit_alias'),
    path('edit/alias', views.AliasCreateView.as_view(), name='edit_alias'),

    path('list/pages', views.PageEditListView.as_view(), name='edit_pages'),
    path('list/links', views.LinkEditListView.as_view(), name='edit_links'),
    path('list/templates', views.TemplateEditListView.as_view(), name='edit_templates'),
    path('list/themes', views.ThemeEditListView.as_view(), name='edit_themes'),
    path('list/aliases', views.AliasEditListView.as_view(), name='list_aliases'),
#    path('edit/arcs', views.ArcEditListView.as_view(), name='edit_arcs'),

    path('', views.ComicView.as_view(), name='index'),
    path('<str:pk>', views.ComicView.as_view(), name='page'),
]
