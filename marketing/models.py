
import uuid
import re

from django.db import models


from snips.models import ModelBase


class Signup(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	email = models.EmailField(unique=True,null=False,blank=False)
	reg_allowed = models.BooleanField(default=False)
	invite_sent = models.DateField(null=True,blank=True)
	status = models.CharField(max_length=1,default='N') # N = new

	@property
	def email_domain(self):
		return re.search("@[\w.]+", self.email).group()[1:]

	def __str__(self):
		return self.email

	class Meta:
		permissions = (('view_signup', "Can view signups"),)

	class Admin:
		pass