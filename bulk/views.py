from django.views.generic import RedirectView, TemplateView, ListView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

from profiles.models import Profile
from profiles.views import ProfileContext
from .models import ConfigSetting

class IndexView(RedirectView):

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linksentry')

#-----------------------------------------------------------------------------#

class ErrorView(ProfileContext, TemplateView):
	''' Inserts http status code into response '''

	status = None

	def render_to_response(self, context, **response_kwargs):
		if self.status is None:
			raise ImproperlyConfigured("ErrorView requires definition of status")

		return super(ErrorView,self).render_to_response(context, status = self.status)

class Error404View(ErrorView):
	template_name = '404.html'
	status = 404

class Error500View(ErrorView):
	status=500
	template_name = '500.html'

#-----------------------------------------------------------------------------#

class ConfigSettingListView(PermissionRequiredMixin, ListView):
	model = ConfigSetting
	permission_required = 'bulk.view_config_setting'

