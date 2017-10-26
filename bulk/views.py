from django.views.generic import RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse

class IndexView(RedirectView):

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linksentry')