from django.views.generic import RedirectView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from links.views import ProfileContext

class IndexView(RedirectView):

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linksentry')

class Error404View(ProfileContext, TemplateView):
	template_name = '404.html'

class Error500View(ProfileContext, TemplateView):
	template_name = '500.html'
