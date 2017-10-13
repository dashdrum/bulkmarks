from django.views.generic import RedirectView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse

class IndexView(RedirectView):

	def get_redirect_url(self, *args, **kwargs):

		if self.request.user.is_authenticated():
			return reverse('userlinks')
		else:
			return reverse('publiclinks')