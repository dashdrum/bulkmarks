from django.contrib import admin

# Register your models here.
from .models import Signup

class SignupAdmin(admin.ModelAdmin):
    readonly_fields = ('created_on','updated_on','id')

    def get_ordering(self, request):
        return ['-created_on']

admin.site.register(Signup,SignupAdmin)