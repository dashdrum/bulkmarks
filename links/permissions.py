from rest_framework.permissions import DjangoModelPermissions

## This class is used as the DEFAULT_PERMISSION_CLASS in settings.py
class DjangoViewModelPermissions(DjangoModelPermissions):

	perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

# class MergePermissions(DjangoModelPermissions):

# 	perms_map = {
#         'GET': ['merge.can_merge'],
#         'OPTIONS': [],
#         'HEAD': [],
#         'POST':  ['merge.can_merge'],
#         'PUT': [],
#         'PATCH': [],
#         'DELETE': [],
#     }