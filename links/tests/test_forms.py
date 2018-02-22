


from datetime import datetime, timedelta, date

from django.test import TestCase


from .factories import (LinkFactory, ProfileFactory, InterfaceFileFactory, UserFactory)

from links.forms import (ProfileForm, LinkForm, ImportFileForm, ExportFileForm,
					ActiveUserInputForm, OtherUserInputForm, DeleteUserLinksInputForm,
					SearchInputForm, TagInputForm)

from urllib.error import URLError
from django.forms import ValidationError

# from training.models import TrainingSchedule



class LinkTestCase(TestCase):
	pass

class TestProfileForm(LinkTestCase):

	def test_validate(self):
		data={'display_name': 'New display name',
			  'acct_public': True,
			  'public_default': False,
			  'first_name': 'new first name',
			  'last_name': 'new last name',
			  'email': 'newemail@bulkmakrs.com',}
		form = ProfileForm(data=data)
		self.assertTrue(form.is_valid())

	def test_save_form(self):
		p = ProfileFactory.create()
		data={'display_name': 'New display name',
			  'acct_public': True,
			  'public_default': False,
			  'first_name': 'new first name',
			  'last_name': 'new last name',
			  'email': 'newemail@bulkmakrs.com',}
		form = ProfileForm(data=data, instance=p)
		form.save()
		self.assertEqual(p.display_name,'New display name' )
		self.assertEqual(p.user.email, 'newemail@bulkmakrs.com')
		self.assertEqual(p.user.first_name, 'new first name')
		self.assertEqual(p.user.last_name, 'new last name')

class TestLinkForm(LinkTestCase):

	def test_clean(self):
		profile = ProfileFactory.create()
		data={'title': '',
			  'url': 'http://bulkmarks.com',
			  'comment': '',
			  'public': '',
			  'tags': '',
			  'profile': profile.pk,}
		form = LinkForm(data=data,current_user_profile=profile)
		self.assertTrue(form.is_valid())

		data={'title': '',
			  'url': 'http://nope.bulkmarks.com',
			  'comment': '',
			  'public': '',
			  'tags': '',
			  'profile': profile.pk,}
		form = LinkForm(data=data,current_user_profile=ProfileFactory.create())
		self.failIf(form.is_valid())
		self.assertIn('Title is required',form.errors['title'])

class TestImportFileForm(LinkTestCase):

	def test_validate_import_format(self):
		data={'import_file': '',
		      'import_format': 'Y',}
		form = ImportFileForm(data=data)
		self.failIf(form.is_valid())
		self.assertIn('Select a valid choice. Y is not one of the available choices.',form.errors['import_format'])

class TestActiveUserInputForm(LinkTestCase):

	def test_user_query(self):
		u1 = UserFactory.create(is_active=True)
		u2 = UserFactory.create(is_active=False)
		u3 = UserFactory.create(is_active=True)

		data = {'user_select': u1.id}
		form = ActiveUserInputForm(data=data)
		self.assertTrue(form.is_valid())

		data = {'user_select': u2.id}
		form = ActiveUserInputForm(data=data)
		self.assertFalse(form.is_valid())

class TestOtherUserInputForm(LinkTestCase):

	def test_user_query(self):
		p1 = ProfileFactory(acct_public=True)
		p2 = ProfileFactory(acct_public=False)

		data = {'user_select': p1.user.id}
		form = OtherUserInputForm(data=data)
		self.assertTrue(form.is_valid())

		data = {'user_select': p2.user.id}
		form = OtherUserInputForm(data=data)
		self.assertFalse(form.is_valid())








