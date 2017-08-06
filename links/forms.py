from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError, ContentTooShortError

from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField)

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField
from bs4 import BeautifulSoup

from .models import Link, Profile
from .choices import IMPORT_TYPE_CHOICES

def get_title(url):
	error_code = None
	title = None

	try:
		## Need to change the agent to fool sites that want to block python bots
		page = urlopen(Request(url,headers={'User-Agent': 'Mozilla'}))
		try:
			soup = BeautifulSoup(page,'html.parser')
			try:
				title = soup.title.string.encode('utf-8')
				return title, '200'
			except:
				error_code = '404'
		except:
			print('Beautiful Soup Error')
			error_code = '500'
			raise  #  Need to find out what errors BS4 will raise
	except HTTPError as e:
		print("HTTPError:", e.reason)
		error_code = e.code
	except URLError as e:
		print("URLError:", e.reason)
		error_code = '400'
	except ContentTooShortError as e:
		error_code = 500

	return None, error_code


class LinkForm(ModelForm):

	title = CharField(required=False)

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