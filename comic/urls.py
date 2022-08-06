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

    path('edit/pages', views.PageEditListView.as_view(), name='edit_pages'),


    path('', views.ComicView.as_view(), name='index'),
    path('<str:pk>', views.ComicView.as_view(), name='page'),
]
