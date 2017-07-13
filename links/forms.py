from django.forms import (ModelForm, ValidationError, Textarea, CharField, Form, FileField, ChoiceField)

from annoying.functions import get_object_or_None
from snips.fields import EmptyChoiceField

from .models import Link, Profile
from .choices import IMPORT_TYPE_CHOICES

class LinkForm(ModelForm):

	class Meta:
		model = Link
		fields = ['title','url','comment','public',]

class ImportFileForm(Form):

	import_file = FileField(allow_empty_file=False,required=True)
	import_type = EmptyChoiceField(required=True,choices=IMPORT_TYPE_CHOICES)

