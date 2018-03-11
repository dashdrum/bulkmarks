

from .models import Profile




def get_profile(user):
	try:
		profile = Profile.objects.get(user = user)
		return profile
	except:
		profile = Profile(user=user,display_name=user.username)
		profile.save()
		return profile