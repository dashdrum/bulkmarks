from django.conf.urls import url, include
from django.contrib.auth.views import (PasswordResetView, PasswordResetDoneView, PasswordResetCompleteView,
									   PasswordResetConfirmView, )

from .views import (ProfileDetailView, ProfileUpdateView, RegistrationView, AccountActivationSent, ActivateView,
	                BulkPasswordChangeView, )

urlpatterns = [

	url(r'^profiledetail/(?P<pk>[0-9A-Fa-f-]+)/$',ProfileDetailView.as_view(),name='profiledetail'),
	url(r'^profileupdate/(?P<pk>[0-9A-Fa-f-]+)/$',ProfileUpdateView.as_view(),name='profileupdate'),


	url(r'^change-password/$', BulkPasswordChangeView.as_view(
			template_name='password_change_form.html',
			success_url='/' ),
		name='password_change'),

	url(r'^password_reset/$', PasswordResetView.as_view(template_name='password_reset_form.html'), name='password_reset'),
	url(r'^password_reset/done/$', PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
	url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
		PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
	url(r'^reset/done/$', PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),

    url(r'^registration/$', RegistrationView.as_view(), name='registration'),
    url(r'^account_activation_sent/$', AccountActivationSent.as_view(), name='account_activation_sent'),
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        ActivateView.as_view(), name='activate'),
]
