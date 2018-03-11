from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField,
	ModelChoiceField, HiddenInput, EmailField, )
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField

from .models import Profile

class ProfileForm(ModelForm):

	first_name = CharField(required=False)
	last_name = CharField(required=False)
	email = EmailField(required=True)

	def save(self, commit=True):
		# Save Profile information
		super(ProfileForm,self).save(commit)

		# Save User information
		user = self.instance.user
		user.first_name = self.cleaned_data.get('first_name',None)
		user.last_name = self.cleaned_data.get('last_name',None)
		user.email = self.cleaned_data.get('email',None)
		user.save()

		return self.instance

	class Meta:
		model = Profile
		fields = ['display_name','acct_public','public_default']

class SignUpForm(UserCreationForm):
	email = EmailField(max_length=254, help_text='Enter a valid email address.')

	class Meta:
		model = User
		fields = ('username', 'email', 'password1', 'password2', )