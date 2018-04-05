from django.contrib import admin

# Register your models here.

from .models import ConfigSetting

admin.site.register(ConfigSetting)