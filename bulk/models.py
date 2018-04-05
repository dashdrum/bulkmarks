
import uuid

from django.db import models


from snips.models import ModelBase


class ConfigSetting(ModelBase):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	config_code = models.CharField(max_length=6,blank=False,null=False,unique=True)
	config_description = models.CharField(max_length=100,blank=False,null=False)
	config_value = models.CharField(max_length=200,blank=False,null=False)

	def __str__(self):
		return self.config_code + ' - ' + self.config_description

	class Meta:
		permissions = (('view_config_seting', "Can view configuration"),)
		ordering = ['config_code']

	class Admin:
		pass
