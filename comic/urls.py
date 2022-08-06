from django.urls import path


from . import views

app_name = 'comic'

urlpatterns = [
    path('', views.ComicView.as_view(), name='index'),
    path('<str:pk>', views.ComicView.as_view(), name='page'),
    path('authors', views.index, name='authors'),
    path('forum', views.index, name='forum'),
    path('archive', views.index, name='archive'),
]
