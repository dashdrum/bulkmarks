from datetime import datetime

from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework.fields import empty

from .models import Link, Profile
from .utils import get_title, check_duplicate_link, get_profile, test_link

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

	def validate_title(self, value):
		"""
		If no title is supplied, get one based on the URL
		"""

		error_code = None

		url = self.initial_data.get('url',None)

		if value is None:
			value, error_code = get_title(url)

		if value is None:
			raise serializers.ValidationError('Title field is required')

		return value

	class Meta:
		model = Link
		fields = ('id','title','url','comment','public','profile','status','tested_on')


class AddURLLinkSerializer(LinkSerializer):

	''' get profile for user, then check for duplicate'''

	def validate(self,data):

		url = data['url']

		# user = self.request.user
		user = User.objects.get(username='dgentry')
		profile = get_profile(user)

		data['profile'] = profile

		# check for duplicate link

		if check_duplicate_link(url,profile):
			raise serializers.ValidationError('Link already saved for this user')

		return data

	class Meta:
		model = Link
		fields = ('id','title','url','comment','public','tags')


class TestLinkSerializer(LinkSerializer):

	def validate(self,data):

		id = data['id']

		data['status'] = test_link(id)
		data['tested_on'] = datetime.now()

		return data

	class Meta:
		model = Link
		fields = ('id','status','tested_on')
		lookup_field = 'id'

