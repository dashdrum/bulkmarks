from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.views import (PasswordChangeView, PasswordResetView, PasswordResetDoneView,
										PasswordResetCompleteView, PasswordResetConfirmView, )
from django.http import Http404

from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView, DeleteView, )
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import redirect
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.conf import settings

from .models import Profile
from .forms import (ProfileForm, SignUpForm)
from .utils import get_profile
from .tokens import account_activation_token
from .tasks import send_activation_email


class ProfileContext(object):

	def get_context_data(self, **kwargs):

		context = super(ProfileContext,self).get_context_data(**kwargs)

		if self.request.user.is_authenticated:
			context['profile'] = get_profile(self.request.user)

		return context


class ProfileDetailView(LoginRequiredMixin, ProfileContext, DetailView):
	model = Profile

	def get_object(self, queryset=None):

		object = super(ProfileDetailView,self).get_object(queryset)

		user = self.request.user

		if user == object.user:
			return object

		raise Http404()

class ProfileUpdateView(LoginRequiredMixin, ProfileContext, UpdateView):
	model = Profile
	form_class = ProfileForm

	def get_object(self, queryset=None):

		object = super(ProfileUpdateView,self).get_object(queryset)

		user = self.request.user

		if user == object.user:
			return object

		raise Http404()

	def get_success_url(self):
		return reverse('index')

	def get_initial(self):

		initial = super(ProfileUpdateView,self).get_initial()

		initial['first_name'] = self.object.user.first_name
		initial['last_name'] = self.object.user.last_name
		initial['email'] = self.object.user.email

		return initial

class BulkPasswordChangeView(ProfileContext, PasswordChangeView):
	pass

class BulkPasswordResetView(ProfileContext, PasswordResetView):
	pass

class BulkPasswordResetDoneView(ProfileContext, PasswordResetDoneView):
	pass

class BulkPasswordResetCompleteView(ProfileContext, PasswordResetCompleteView):
	pass

class BulkPasswordResetConfirmView(ProfileContext, PasswordResetConfirmView):
	pass

class SignupView(ProfileContext, FormView):
	form_class = SignUpForm
	template_name = 'signup.html'

	def form_valid(self,form):
		user = form.save(commit=False)
		user.is_active = False
		user.save()

		try:
			profile = Profile.objects.get(user=user)
			display_name = form.cleaned_data.get('display_name',None)
			if display_name:
				profile.display_name = display_name
				profile.save()
		except Profile.DoesNotExist:
			None

		if settings.USE_CELERY:
			send_activation_email.delay(user,self.request)
		else:
			send_activation_email(user,self.request)

		return super(SignupView,self).form_valid(form)

	def form_invalid(self, form):
		''' Catch username, email, and password match, resend '''

		try:
			username = form['username'].value()
			password = form['password1'].value()
			email = form['email'].value()
			user = User.objects.get(username=username)
			if user.username == username and user.email == email \
			and user.check_password(password) and not user.is_active:
			 ## Resending email
				if settings.USE_CELERY:
					send_activation_email.delay(user,self.request)
				else:
					send_activation_email(user,self.request)

				return super(SignupView,self).form_valid(form) ## We can do better
		except Exception as e:
			print('SignupView.form_invalid()',type(e),e.args)

		return super(SignupView,self).form_invalid(form)

	def get_success_url(self):
		return reverse('account_activation_sent')

class AccountActivationSent(ProfileContext, TemplateView):
	template_name = 'account_activation_sent.html'

class ActivateView(ProfileContext, TemplateView):
	template_name = 'account_activation_invalid.html'

	def get(self,request,*args,**kwargs):
		uidb64 = self.kwargs.get('uidb64',None)
		token = self.kwargs.get('token',None)
		try:
			uid = force_text(urlsafe_base64_decode(uidb64))
			user = User.objects.get(pk=uid)
			if user.is_active:  ## Already authenticated
				raise ValueError
		except (TypeError, ValueError, OverflowError, User.DoesNotExist):
			user = None

		if user is not None and account_activation_token.check_token(user, token):
			user.is_active = True
			user.profile.email_confirmed = True
			user.save()
			login(request, user)
			profile = get_profile(user)
			return redirect('profileupdate',str(profile.id))
		else:
			return super(ActivateView,self).get(request,*args,**kwargs)




