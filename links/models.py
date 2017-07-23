from django.db import models
from django.core.urlresolvers import reverse

from snips.models import ModelBase
from annoying.functions import get_object_or_None

#from django.contrib.auth.models import User
from django.conf import settings

from datetime import datetime
try:
    from django.utils.timezone import now
except ImportError:
    from datetime.datetime import now

import uuid

class Link(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=200,blank=False,null=False)
	url = models.URLField(max_length=400,blank=False,null=False)
	comment = models.TextField(max_length=1000, null=True, blank=True)
	public = models.BooleanField(default=True)
	status = models.CharField(max_length=1,blank=True,null=True) # Not found, OK, Redirect, Error
	profile = models.ForeignKey('Profile',null=False,blank=False)
	tested_on = models.DateTimeField(blank=True,null=True)

	@property
	def user(self):
		return self.profile.user

	def __str__(self):
		return self.title

	class Meta:
		permissions = (('view_links', "Can view links"),)

	class Admin:
		pass

class Profile(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(settings.AUTH_USER_MODEL,null=False)
	public_default = models.BooleanField(default=True)
	acct_public = models.BooleanField(default=True)
	display_name = models.CharField(max_length=200,null=False,blank=False)
	email = models.EmailField(null=False,blank=False)
	url = models.URLField(max_length=400,blank=True,null=True)
	notes = models.TextField(max_length=1000, null=True, blank=True)

	def __str__(self):
		return self.display_name

	class Meta:
		permissions = (('view_profiles',"Can view profiles"),)

	class Admin:
		pass

class InterfaceFile(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	profile = models.ForeignKey('Profile',null=False,blank=False)
	file_name = models.CharField(max_length=500,null=True,blank=True)
	file_type = models.CharField(max_length=1, null=False,blank=False)
	text = models.TextField(null=False,blank=True)
	file_format = models.CharField(max_length=1,null=False,blank=False) # Delicious, others TBA - maybe OPML and HTML
	status = models.CharField(max_length=1,null=False,blank=False,default='N') # No, Yes, Error

	def __str__(self):
		return self.profile.display_name + ' ' + self.created_on.strftime('%Y-%m-%d %H:%M:%S')

	class Meta:
		permissions = (('view_interface_files',"Can view interface files"),)

	class Admin:
		pass

