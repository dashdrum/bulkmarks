from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField,
	ModelChoiceField,)
from django.contrib.auth.models import User

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField

from .models import Link, Profile
from .choices import IMPORT_TYPE_CHOICES
from .utils import get_title


class LinkForm(ModelForm):

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
		fields = ['title','url','comment','public',]

class ImportFileForm(Form):

	import_file = FileField(allow_empty_file=False,required=True)
	import_type = EmptyChoiceField(required=True,choices=IMPORT_TYPE_CHOICES)

class ExportFileForm(Form):
	pass

class UserInputForm(ModelForm):

	user_select = ModelChoiceField(required=True,
		queryset=User.objects.filter(is_active=True),
		label = 'View another user\'s public links' )

	class Meta:
		model = User
		fields = ['user_select',]
