from django.contrib import admin

# Register your models here.

from .models import Link, Profile, InterfaceFile

class LinkAdmin(admin.ModelAdmin):
    readonly_fields = ('created_on','updated_on','id')

    def get_ordering(self, request):
        return ['-created_on']

class ProfileAdmin(admin.ModelAdmin):
    readonly_fields = ('created_on','updated_on','id')

class InterfaceFileAdmin(admin.ModelAdmin):
    readonly_fields = ('created_on','updated_on','id')

admin.site.register(Link,LinkAdmin)
admin.site.register(Profile,ProfileAdmin)
admin.site.register(InterfaceFile,InterfaceFileAdmin)
