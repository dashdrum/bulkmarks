from datetime import datetime

from rest_framework import serializers
from rest_framework.fields import empty

from .models import Link, Profile
from .forms import get_title

class TitleCharField(serializers.CharField):

	def validate_empty_values(self, data):

		''' If the field is not provided, allow validation to continue '''

		if data is empty:
			return (True,None)

		if data is None:
			return (True, None)

		return (False, data)


class LinkSerializer(serializers.ModelSerializer):

	title = TitleCharField(max_length=200)
	#profile = serializers.PrimaryKeyRelatedField(queryset=Profile.objects.all(),required=False)

	# def validate_title(self, value):
	# 	"""
	# 	If no title is supplied, get one based on the URL
	# 	"""

	# 	error_code = None

	# 	url = self.initial_data.get('url',None)

	# 	if value is None:
	# 		value, error_code = get_title(url)

	# 	if value is None:
	# 		raise serializers.ValidationError('Title field is required')

	# 	return value

	class Meta:
		model = Link
		fields = ('id','title','url','comment','public','profile','status','tested_on')


class AddURLLinkSerializer(LinkSerializer):

	class Meta:
		model = Link
		fields = ('id','title','url','comment','public')


class TestLinkSerializer(LinkSerializer):

	class Meta:
		model = Link
		fields = ('id','status','tested_on')
		lookup_field = 'id'

