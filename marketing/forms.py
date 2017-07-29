
from django.forms import (ModelForm, ValidationError, )

from annoying.functions import get_object_or_None

from .models import Signup
from links.models import Profile

class SignupQuickForm(ModelForm):

	def clean_email(self):

		email = self.cleaned_data['email']

		if email:
			try:
				profile = Profile.objects.get(email=email)
				raise ValidationError('Email already registered')
			except Profile.DoesNotExist:
				pass  #  This is OK

		return email

	class Meta:
		model = Signup
		fields = ['email',]
