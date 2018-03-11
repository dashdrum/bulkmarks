from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.models import User

from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView, DeleteView, )
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string

from .models import Profile
from .forms import (ProfileForm, SignUpForm)
from .utils import get_profile
from .tokens import account_activation_token


class ProfileContext(object):

	def get_context_data(self, **kwargs):

		context = super(ProfileContext,self).get_context_data(**kwargs)

		if self.request.user.is_authenticated:
			context['profile'] = get_profile(self.request.user)

		return context


class ProfileDetailView(LoginRequiredMixin, ProfileContext, DetailView):
	model = Profile

class ProfileUpdateView(LoginRequiredMixin, ProfileContext, UpdateView):
	model = Profile
	form_class = ProfileForm

	def get_success_url(self):
		return reverse('profiledetail' , kwargs={'pk': self.object.id })

	def get_initial(self):

		initial = super(ProfileUpdateView,self).get_initial()

		initial['first_name'] = self.object.user.first_name
		initial['last_name'] = self.object.user.last_name
		initial['email'] = self.object.user.email

		return initial

def signup(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save(commit=False)
			user.is_active = False
			user.save()
			current_site = get_current_site(request)
			subject = 'Activate Your MySite Account'
			message = render_to_string('account_activation_email.html', {
				'user': user,
				'domain': current_site.domain,
				'uid': urlsafe_base64_encode(force_bytes(user.pk)),
				'token': account_activation_token.make_token(user),
			})
			user.email_user(subject, message)
			return redirect('account_activation_sent')
	else:
		form = SignUpForm()
	return render(request, 'signup.html', {'form': form})

def account_activation_sent(request):
	return render(request, 'account_activation_sent.html')


def activate(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except (TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None

	if user is not None and account_activation_token.check_token(user, token):
		user.is_active = True
		user.profile.email_confirmed = True
		user.save()
		login(request, user)
		return redirect('index')
	else:
		return render(request, 'account_activation_invalid.html')