"""bulk URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
	https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
	1. Import the include() function: from django.conf.urls import url, include
	2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf.urls import handler404, handler500
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage

from .views import IndexView, Error404View, Error500View

urlpatterns = [
	url(
		r'^favicon.ico$',
		RedirectView.as_view(
			url=staticfiles_storage.url('favicon.ico'),
			permanent=False),
		name="favicon"
	),
	url(r'^a/', admin.site.urls),
	url(r'^l/', include('links.urls')),
	url(r'^m/', include('marketing.urls')),

	url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'),name='login'),
	url(r'^logout/$', auth_views.LogoutView.as_view(),name='logout'),
	url(r'^change-password/$', auth_views.PasswordChangeView.as_view(
			template_name='password_change_form.html',
			success_url='/' ),
		name='password_change'),

	url(r'^password_reset/$', auth_views.PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
	url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
	url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
		auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
	url(r'^reset/done/$', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

	url(r'^$',IndexView.as_view(),name='index'),
]

###  Django Debug Toolbar

from django.conf import settings

if 'debug_toolbar' in settings.INSTALLED_APPS:
	from debug_toolbar import urls as debug_urls
	urlpatterns.append(url(r'^__debug__/',include(debug_urls)))

### Heartbeat

if 'heartbeat' in settings.INSTALLED_APPS:
  from heartbeat.urls import urlpatterns as heartbeat_urls

  urlpatterns += [
	url(r'^heartbeat/', include(heartbeat_urls))
  ]


handler404 = Error404View.as_view()
handler500 = Error500View.as_view()
