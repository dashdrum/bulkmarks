from django.conf.urls import url, include

from rest_framework import routers

from .views import (LinkListView, LinkDetailView, LinkCreateView, LinkUpdateView,
					UploadImportFileTemplateView, TestLinkView, VisitLinkView,
					ExportLinksView, LinkDeleteView, SearchLinkListView,
					TestAllLinksView, DeleteUserLinksView, TagLinkListView,  )

from .views import link_create
from .views import (GetTitleAPIView, AddURLAPIView, TestLinkAPIView,)
from .views import AddURLViewSet

router = routers.DefaultRouter()
router.register(r'api/links', AddURLViewSet)

urlpatterns = [
	url(r'^links/$', LinkListView.as_view(), name='linksentry'),
	url(r'^links/(?P<scope>.*)/$', LinkListView.as_view(), name='links'),
	url(r'^taglinks/(?P<scope>.*)/(?P<tag>.*)/$', TagLinkListView.as_view(), name='taglinks'),
	url(r'^taglinks/$', TagLinkListView.as_view(), name='tagentry'),
	url(r'^linkcreate/$', LinkCreateView.as_view(), name='linkcreate'),
	url(r'^linkcreate/(?P<pk>[0-9A-Fa-f-]+)/$', LinkCreateView.as_view(), name='linkcopy'),
	url(r'^linkvisit/(?P<pk>[0-9A-Fa-f-]+)/$',VisitLinkView.as_view(),name='linkvisit'),
	url(r'^linkdetail/(?P<pk>[0-9A-Fa-f-]+)/$',LinkDetailView.as_view(),name='linkdetail'),
	url(r'^linkupdate/(?P<pk>[0-9A-Fa-f-]+)/$',LinkUpdateView.as_view(),name='linkupdate'),
	url(r'^linkdelete/(?P<pk>[0-9A-Fa-f-]+)/$',LinkDeleteView.as_view(),name='linkdelete'),
	url(r'^linktest/(?P<pk>[0-9A-Fa-f-]+)/$',TestLinkView.as_view(),name='linktest'),
	url(r'^linktestall/$', TestAllLinksView.as_view(), name='linktestall'),
	url(r'^import/$', UploadImportFileTemplateView.as_view(), name='import'),
	url(r'^export/$', ExportLinksView.as_view(), name='export'),
	url(r'^search/$', SearchLinkListView.as_view(), name='searchentry'),
	url(r'^search/(?P<scope>.*)/(?P<searchparam>.*)/$', SearchLinkListView.as_view(), name='search'),

	## Admin links

	url(r'^deleteuserlinks/$', DeleteUserLinksView.as_view(), name='deleteuserlinks'),

	## Modal dialogs

	url(r'^create/$',link_create, name='link_create'),

	## API

	url(r'^', include(router.urls)),

	url(r'^api/gettitle/$',GetTitleAPIView.as_view(),name='gettitle'),
	url(r'^api/addurl/$',AddURLAPIView.as_view(),name='addurl'),
	url(r'^api/testlink/$',TestLinkAPIView.as_view(),name='testlink'),
]
