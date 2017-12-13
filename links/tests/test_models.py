


from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
#from datetime import date, time
from datetime import datetime, timedelta
from django.utils import timezone



from .factories import (LinkFactory, ProfileFactory, InterfaceFileFactory)

#### Testing the Models


class LinkTestCase(TestCase):
	pass

class TestLinkModel(LinkTestCase):

	def test_property_user(self):
		l = LinkFactory.create()
		self.assertEqual(l.user, l.profile.user)

	def test_str(self):
		l = LinkFactory.create()
		self.assertTrue(l.__str__(),l.title)

	def test_status_label(self):
		l = LinkFactory.create(status='O')
		self.assertEqual(l.status_label,'OK')

	def test_save(self):
		l = LinkFactory.create(url='https://www.nmc.edu',title=None)
		self.assertEqual(l.title, 'NMC : Northwestern Michigan College')

		l = LinkFactory.create(title='this title')
		self.assertEqual(l.title, 'this title')

	def test_clean(self):
		l = LinkFactory.create()
		l2 = LinkFactory.create()
		l2.url = l.url
		l2.profile = l.profile
		self.assertRaises(ValidationError, l2.full_clean)

class TestProfileModel(LinkTestCase):
	def test_defaults(self):
		p = ProfileFactory.create()
		self.assertTrue(p.public_default)
		self.assertTrue(p.acct_public)

		p = ProfileFactory.create(public_default = False, acct_public = False)
		self.assertFalse(p.public_default)
		self.assertFalse(p.acct_public)

	def test_str(self):
		p = ProfileFactory.create(display_name = 'this text')
		self.assertEqual(p.__str__(),'this text')

class TestInterfaceFileModel(LinkTestCase):
	def test_default(self):
		i = InterfaceFileFactory.create()
		self.assertEqual(i.status,'N')

	def test_file_format_label(self):
		i = InterfaceFileFactory.create(file_format='D')
		self.assertEqual(i.file_format_label,'Delicious Export File')

	def test_str(self):
		t = timezone.now()
		p = ProfileFactory(display_name = 'this name')
		i = InterfaceFileFactory.create(profile = p,created_on = t)
		test_value = 'this name' + ' ' + t.strftime('%Y-%m-%d %H:%M:%S')
		self.assertEqual(i.__str__(),test_value)


