from django.shortcuts import render

# Create your views here.

from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView)
from django.urls import reverse

from django.conf import settings

from .forms import SignupQuickForm
from .models import Signup
from .tasks import send_signup_email


class SignupQuickCreateView(CreateView):
	model = Signup
	form_class = SignupQuickForm

	def get_success_url(self):
		return reverse('index')

	def form_valid(self,form):

		email = form.cleaned_data['email']

		if settings.USE_CELERY:
			send_signup_email.delay(email)
		else:
			send_signup_email(email)

		return super(SignupQuickCreateView,self).form_valid(form)