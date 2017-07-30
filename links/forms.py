import urllib

from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField)

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField
from bs4 import BeautifulSoup

from .models import Link, Profile
from .choices import IMPORT_TYPE_CHOICES

def get_title(url):
	soup = BeautifulSoup(urllib.request.urlopen(url),"html.parser")
	return soup.title.string.encode('utf-8')

class LinkForm(ModelForm):

	title = CharField(required=False)

	def clean(self):

		cleaned_data = super(LinkForm, self).clean()

		title = cleaned_data.get('title',None)
		url = cleaned_data.get('url',None)

		if not title:
			if url:
				title = get_title(url)

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