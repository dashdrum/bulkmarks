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

class SignupView(FormView):
	form_class = SignUpForm
	template_name = 'signup.html'

	def form_valid(self,form):
		user = form.save(commit=False)
		user.is_active = False
		user.save()

		current_site = get_current_site(self.request)
		subject = 'Activate Your Bulkmarks Account'
		message = render_to_string('account_activation_email.html', {
			'user': user,
			'domain': current_site.domain,
			'uid': urlsafe_base64_encode(force_bytes(user.pk)),
			'token': account_activation_token.make_token(user),
		})
		user.email_user(subject, message)

		return super(SignupView,self).form_valid(form)

	def get_success_url(self):
		return reverse('account_activation_sent')

class AccountActivationSent(TemplateView):
	template_name = 'account_activation_sent.html'

class ActivateView(TemplateView):
	template_name = 'account_activation_invalid.html'

	def get(self,request,*args,**kwargs):
		uidb64 = self.kwargs.get('uidb64',None)
		token = self.kwargs.get('token',None)
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
			return super(ActivateView,self).get(request,*args,**kwargs)




