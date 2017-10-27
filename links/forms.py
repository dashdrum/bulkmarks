from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField,
	ModelChoiceField, HiddenInput)
from django.contrib.auth.models import User

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField

from .models import Link, Profile
from .choices import IMPORT_TYPE_CHOICES
from .utils import get_title


class LinkForm(ModelForm):

	def __init__(self, *args, **kwargs):
		super(LinkForm, self).__init__(*args, **kwargs)
		##  Setting field attributes in __init__ avoids having to specify the field type, uses default
		self.fields['tags'].required=False

	title = CharField(required=False)
	comment = CharField(required=False,widget=Textarea(attrs={'rows': '3'}))

	def clean(self):

		cleaned_data = super(LinkForm, self).clean()

		title = cleaned_data.get('title',None)
		url = cleaned_data.get('url',None)

		error_code = None

		if not title:
			if url:
				title, error_code = get_title(url)

		if not title:
			raise ValidationError('Title is required')

		cleaned_data['title'] = title

		return cleaned_data

	class Meta:
		model = Link
		fields = ['title','url','comment','public','tags',]

class ImportFileForm(Form):

	import_file = FileField(allow_empty_file=False,required=True)
	import_type = EmptyChoiceField(required=True,choices=IMPORT_TYPE_CHOICES)

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

