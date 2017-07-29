from django.shortcuts import render

# Create your views here.

from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView)
from django.core.urlresolvers import reverse

from .forms import SignupQuickForm
from .models import Signup


class SignupQuickCreateView(CreateView):
	model = Signup
	form_class = SignupQuickForm

	def get_success_url(self):
		return reverse('index')