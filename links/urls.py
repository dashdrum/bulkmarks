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
from django.conf.urls import url
from .views import (UserLinkListView, LinkDetailView, LinkCreateView, LinkUpdateView,
					UploadImportFileTemplateView, TestLinkView, VisitLinkView,
					ExportLinksView, LinkDeleteView,SearchLinkListView,
					TestAllLinksView,)
from .views import link_create
from .views import (GetTitleAPIView, AddURLAPIView, TestLinkAPIView,)

urlpatterns = [
	url(r'^userlinks/$', UserLinkListView.as_view(), name='userlinks'),
	url(r'^linkcreate/$', LinkCreateView.as_view(), name='linkcreate'),
	url(r'^linkvisit/(?P<pk>[0-9A-Fa-f-]+)/$',VisitLinkView.as_view(),name='linkvisit'),
	url(r'^linkdetail/(?P<pk>[0-9A-Fa-f-]+)/$',LinkDetailView.as_view(),name='linkdetail'),
	url(r'^linkupdate/(?P<pk>[0-9A-Fa-f-]+)/$',LinkUpdateView.as_view(),name='linkupdate'),
	url(r'^linkdelete/(?P<pk>[0-9A-Fa-f-]+)/$',LinkDeleteView.as_view(),name='linkdelete'),
	url(r'^linktest/(?P<pk>[0-9A-Fa-f-]+)/$',TestLinkView.as_view(),name='linktest'),
	url(r'^linktestall/$', TestAllLinksView.as_view(), name='linktestall'),
	url(r'^import/$', UploadImportFileTemplateView.as_view(), name='import'),
	url(r'^export/$', ExportLinksView.as_view(), name='export'),
	url(r'^search/$', SearchLinkListView.as_view(), name='search'),

	## Modal dialogs

	url(r'^create/$',link_create, name='link_create'),

	## API

	url(r'^api/gettitle/$',GetTitleAPIView.as_view(),name='gettitle'),
	url(r'^api/addurl/$',AddURLAPIView.as_view(),name='addurl'),
	url(r'^api/testlink/$',TestLinkAPIView.as_view(),name='testlink'),
]
