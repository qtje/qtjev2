from django.urls import path


from . import views

urlpatterns = [
    path('', views.ComicView.as_view(), name='index'),
    path('<str:pk>', views.ComicView.as_view(), name='index'),
]
