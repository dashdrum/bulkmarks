from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField,
	ModelChoiceField, HiddenInput, EmailField, )
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField

from .models import Profile
from marketing.models import Signup

class ProfileForm(ModelForm):

	email = EmailField(required=True)

	def save(self, commit=True):
		# Save Profile information
		super(ProfileForm,self).save(commit)

		# Save User information
		user = self.instance.user
		user.email = self.cleaned_data.get('email',None)
		user.save()

		return self.instance

	def clean_email(self):

		email = self.cleaned_data.get('email',None)

		email = email.lower()  ## Force lowercase email

		return email

	class Meta:
		model = Profile
		fields = ['display_name','acct_public','public_default']

class RegistrationForm(UserCreationForm):
	email = EmailField(max_length=254, help_text='Enter a valid email address.')
	display_name = CharField(max_length=200)

	def clean_username(self):

		username = self.cleaned_data.get('username',None)

		## Force username lower case in registration
		return username.lower()

	def clean_email(self):

		email_valid = True

		email = self.cleaned_data.get('email',None)

		email = email.lower()  ## Force lowercase email address

		try:
			User.objects.get(email=email)
			email_valid = False
			self.add_error('email',ValidationError('This email address is already in use.', code='email_in_use'))
		except User.DoesNotExist: # email is not already in use
			pass   # DNE is OK

		try:
			Signup.objects.get(email=email,reg_allowed=True)
		except Signup.DoesNotExist:
			email_valid = False
			self.add_error('email',ValidationError('Registration not yet allowed for this address', code='email_not_allowed'))

		if email_valid:
			return email

	class Meta:
		model = User
		fields = ('username', 'password1', 'password2', 'display_name', 'email')
