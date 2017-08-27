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
from django.contrib import admin
from django.contrib.auth import views as auth_views

from .views import IndexView

urlpatterns = [
    url(r'^a/', admin.site.urls),
    url(r'^l/', include('links.urls')),
    url(r'^m/', include('marketing.urls')),

    url(r'^login/$', auth_views.login,{'template_name': 'login.html'},name='login'),
    url(r'^logout/$', auth_views.logout,{'next_page': '/'},name='logout'),

    url(r'^$',IndexView.as_view(),name='index'),
]

###  Django Debug Toolbar

from django.conf import settings

if 'debug_toolbar' in settings.INSTALLED_APPS:
    from debug_toolbar import urls as debug_urls
    urlpatterns.append(url(r'^__debug__',include(debug_urls)))

### Heartbeat

if 'heartbeat' in settings.INSTALLED_APPS:
  from heartbeat.urls import urlpatterns as heartbeat_urls

  urlpatterns += [
    url(r'^heartbeat/', include(heartbeat_urls))
  ]
