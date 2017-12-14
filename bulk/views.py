from django.views.generic import RedirectView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured

from links.views import ProfileContext

class IndexView(RedirectView):

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linksentry')

class ErrorView(ProfileContext, TemplateView):
	''' Inserts http status code into response '''

	status = None

	def render_to_response(self, context, **response_kwargs):
		if self.status is None:
			raise ImproperlyConfigured("ErrorView requires definition of status")

		# # I don't know why this next line doesn't work
		# return super(ErrorView,self).render_to_response(context,{'status': self.status})

		response_kwargs.setdefault('content_type', self.content_type)
		return self.response_class(
			request=self.request,
			template=self.get_template_names(),
			context=context,
			using=self.template_engine,
			status=self.status,
			**response_kwargs
		)

class Error404View(ErrorView):
	template_name = '404.html'
	status = 404

class Error500View(ErrorView):
	status=500
	template_name = '500.html'
