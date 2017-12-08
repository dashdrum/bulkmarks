
from django.forms import (ModelForm, ValidationError, )

from annoying.functions import get_object_or_None

from .models import Signup
from django.contrib.auth.models import User

class SignupQuickForm(ModelForm):

	def clean_email(self):

		email = self.cleaned_data['email']

		if email:
			try:
				user = User.objects.get(email=email)
				raise ValidationError('Email already registered')
			except User.DoesNotExist:
				pass  #  This is OK

		return email

	class Meta:
		model = Signup
		fields = ['email',]
