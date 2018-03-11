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
import uuid

# Create your models here.


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