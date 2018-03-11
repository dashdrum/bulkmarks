from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView, DeleteView, )

from .models import Profile
from .forms import (ProfileForm, )
from .utils import get_profile


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