from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField,
	ModelChoiceField, HiddenInput, EmailField, )
from django.contrib.auth.models import User

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField

from .models import Link, Profile
from .choices import IMPORT_FORMAT_CHOICES
from .link_utils import get_title

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


class LinkForm(ModelForm):

	def __init__(self, *args, **kwargs):

		super(LinkForm, self).__init__(*args, **kwargs)

		##  Setting field attributes in __init__ avoids having to specify the field type
		self.fields['tags'].required=False
		self.fields['title'].required=False
		self.fields['comment'].required=False
		self.fields['comment'].widget=Textarea(attrs={'rows': '3'})

	def _post_clean(self):
		''' Be sure that the instance's validate_unique is run including the profile field '''
		super(LinkForm,self)._post_clean()
		try:
			self.instance.validate_unique(exclude=None)
		except ValidationError as e:
			self._update_errors(e)

	def clean(self):

		## No need to add the field to the form
		# self.fields['profile'] = ModelChoiceField(Profile.objects.all(),initial=self.profile)

		cleaned_data = super(LinkForm, self).clean()

		## No need to add profile to cleaned_data
		# if self.profile:
		# 	cleaned_data['profile'] = self.profile

		title = cleaned_data.get('title',None)
		url = cleaned_data.get('url',None)

		error_code = None

		if not title:
			if url:
				title, error_code = get_title(url)

		if not title:
			self.add_error('title',ValidationError('Title is required', code='no_title'))

		cleaned_data['title'] = title

		return cleaned_data

	class Meta:
		model = Link
		fields = ['title','url','comment','public','tags']

class ImportFileForm(Form):

	import_file = FileField(allow_empty_file=False,required=True)
	import_format = EmptyChoiceField(required=True,choices=IMPORT_FORMAT_CHOICES)

class ExportFileForm(Form):
	pass

class ActiveUserInputForm(ModelForm):

	user_select = ModelChoiceField(required=True,
		queryset=User.objects.filter(is_active=True))

	class Meta:
		model = User
		fields = ['user_select',]

class OtherUserInputForm(ActiveUserInputForm):

	def __init__(self, *args, **kwargs):
		super(OtherUserInputForm, self).__init__(*args, **kwargs)
		qs = self.fields['user_select'].queryset
		self.fields['user_select'].queryset = qs.filter( profile__acct_public = True)
		self.fields['user_select'].label='View another user\'s public links'

class DeleteUserLinksInputForm(ActiveUserInputForm):

	def __init__(self, *args, **kwargs):
		super(DeleteUserLinksInputForm, self).__init__(*args, **kwargs)
		self.fields['user_select'].label='Delete another user\'s links'

class SearchInputForm(Form):
	scope = CharField(max_length=60,widget=HiddenInput()) # Arbitrary length for now
	searchparam = CharField(max_length=200,label='Search') # Arbitrary length for now

class TagInputForm(Form):
	scope = CharField(max_length=60,widget=HiddenInput()) # Arbitrary length for now
	searchtag = CharField(max_length=100,label='Tag Search') # Arbitrary length for now

