from functools import reduce
import operator

from django.db import models
from django.db.models import Q
from django.urls import reverse

from snips.models import ModelBase
from annoying.functions import get_object_or_None

#from django.contrib.auth.models import User
from django.conf import settings

from datetime import datetime
try:
	from django.utils.timezone import now
except ImportError:
	from datetime.datetime import now

from .link_utils import get_title
from .choices import LINK_STATUS_CHOICES, IMPORT_FORMAT_CHOICES, IMPORT_STATUS_CHOICES

import uuid

#-----------------------------------------------------------------------------#

# Need to modify the through model to use a UUID as the object_id

from taggit.managers import TaggableManager
from taggit.managers import TaggableManager
from taggit.models import CommonGenericTaggedItemBase, TaggedItemBase

class GenericUUIDTaggedItem(CommonGenericTaggedItemBase, TaggedItemBase):
    object_id = models.UUIDField(verbose_name='Object id', db_index=True)

#-----------------------------------------------------------------------------#

class LinkSearchManager(models.Manager):
    def search(self, search_terms):
        terms = [term.strip() for term in search_terms.split()]
        q_objects = []

        for term in terms:
            q_objects.append(Q(title__icontains=term))
            q_objects.append(Q(comment__icontains=term))

        # Start with a bare QuerySet
        qs = self.get_queryset()

        # Use operator's or_ to string together all of your Q objects.
        return qs.filter(reduce(operator.or_, q_objects))

class Link(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=200,blank=True,null=False)
	url = models.URLField(max_length=400,blank=False,null=False)
	comment = models.TextField(max_length=1000, null=True, blank=True)
	public = models.BooleanField(default=True)
	status = models.CharField(max_length=1,blank=True,null=True,choices = LINK_STATUS_CHOICES)
	profile = models.ForeignKey('Profile',null=False,blank=False,on_delete=models.CASCADE)
	tested_on = models.DateTimeField(blank=True,null=True)

	tags = TaggableManager(through=GenericUUIDTaggedItem)

	objects = models.Manager()
	search_objects = LinkSearchManager()

	@property
	def user(self):
		return self.profile.user

	@property
	def status_label(self):
		try:
			return dict(LINK_STATUS_CHOICES)[self.status]
		except KeyError:
			return self.status

	def __str__(self):
		return self.title

	def save(self,*args, **kwargs):
		''' If title is empty, try to get a title from the page
			A null value returned by get_title will trigger the field required
			error '''

		error_code = None

		if self.title is None:
			self.title, error_code = get_title(self.url)

		super(Link, self).save(*args, **kwargs)

	class Meta:
		permissions = (('view_links', "Can view links"),)
		unique_together = ('url','profile')

	class Admin:
		pass

class Profile(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.OneToOneField(settings.AUTH_USER_MODEL,null=False,on_delete=models.CASCADE)
	public_default = models.BooleanField(default=True) # default value for public field on link
	acct_public = models.BooleanField(default=True)    # is account visible to others
	display_name = models.CharField(max_length=200,null=False,blank=False)

	def __str__(self):
		return self.display_name

	class Meta:
		permissions = (('view_profiles',"Can view profiles"),)

	class Admin:
		pass

class InterfaceFile(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	profile = models.ForeignKey('Profile',null=False,blank=False,on_delete=models.CASCADE)
	file_name = models.CharField(max_length=500,null=True,blank=True)
	file_type = models.CharField(max_length=1, null=False,blank=False) # 'I'mport or 'E'xport
	text = models.TextField(null=False,blank=True)
	file_format = models.CharField(max_length=1,null=False,blank=False, choices = IMPORT_FORMAT_CHOICES)
	status = models.CharField(max_length=1,null=False,blank=False,default='N', choices = IMPORT_STATUS_CHOICES)

	@property
	def file_format_label(self):
		try:
			return dict(IMPORT_FORMAT_CHOICES)[self.file_format]
		except KeyError:
			return self.file_format

	def __str__(self):
		return self.profile.display_name + ' ' + self.created_on.strftime('%Y-%m-%d %H:%M:%S')

	class Meta:
		permissions = (('view_interface_files',"Can view interface files"),)

	class Admin:
		pass

