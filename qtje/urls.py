"""qtje URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import django.contrib.auth.views as auth_views

from django.views.static import serve

urlpatterns = [
    path('', include('comic.urls')),
    path(r'admin/', admin.site.urls),

    path('user/password_change', auth_views.PasswordChangeView.as_view(template_name='comic/password_reset.html', extra_context = {'header': 'Password Update', 'button': 'Update'}), name='password_change'),
    path('user/password_change_done', auth_views.PasswordChangeDoneView.as_view(template_name='comic/password_reset.html', extra_context = {'header': 'Password Update', 'information': 'Your password has been updated.'}), name='password_change_done'),

    path('user/password_reset', auth_views.PasswordResetView.as_view(template_name='comic/password_reset.html', extra_context = {'information': 'Enter your email address below. You will receive an email with a link to reset your password.'}), name='password_reset'),

   path('user/password_reset_done', auth_views.PasswordResetDoneView.as_view(template_name='comic/password_reset.html', extra_context = {'information': 'An email was sent to the address you entered.'}), name='password_reset_done'),

   path('user/reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(template_name='comic/password_reset.html'), name='password_reset_confirm'),

   path('user/reset/done', auth_views.PasswordResetCompleteView.as_view(template_name='comic/password_reset.html', extra_context = {'reset_done': True}), name='password_reset_complete'),



]


# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns = [
        re_path(r'^media/(?P<path>.*)$', serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        ] + staticfiles_urlpatterns() + urlpatterns

