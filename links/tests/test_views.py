

from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, AnonymousUser
from django.http.response import Http404
#from datetime import date, time
#from datetime import datetime
from annoying.functions import get_object_or_None

from links.models import Profile, Link, InterfaceFile
from links.views import (LinkListView, TagLinkListView, LinkDetailView, LinkCreateView,
	LinkDeleteView, LinkUpdateView, ProfileDetailView, ProfileUpdateView,
	UploadImportFileTemplateView, ExportLinksView, TestLinkView, TestAllLinksView,
	VisitLinkView, DeleteUserLinksView, SearchLinkListView, )
from .factories import UserFactory, LinkFactory, ProfileFactory, InterfaceFileFactory


test_url = 'https://dashdrum.com'


class LinkTestCase(TestCase):
	# fixtures = ['test_initial_data.json']

	def setUp(self):
		self.client = Client()

		self.normal_user = UserFactory(username='normal',last_name='Normal',first_name='Abbie')
		self.normal_user.set_password('!')
		self.normal_user.save()
		self.normal2_user = UserFactory(username='normal2',last_name='Normal',first_name='Another')
		self.normal2_user.set_password('!')
		self.normal2_user.save()
		self.admin_user = UserFactory(username='admin',is_superuser=True,is_staff=True,first_name='Admin')
		self.admin_user.set_password('!')
		self.admin_user.save()

		self.normal_pro = ProfileFactory(user=self.normal_user,acct_public=True,display_name='Normal')
		self.normal2_pro = ProfileFactory(user=self.normal2_user,acct_public=True,display_name='Normal2')
		self.admin_pro = ProfileFactory(user=self.admin_user,acct_public=False,display_name='Admin Guy')


	def assertNoRaise(self, callableObj=None, *args, **kwargs):
		"""Basically the opposite of assertRaises
		"""
		if callableObj is None:  #  It's gotta be callable
			return _AssertRaisesContext(excClass, self)
		try:
			callableObj(*args, **kwargs)
			return
		except Exception as exc:
			raise self.failureException("%s Exception raised" % type(exc) )

class TestUsers(LinkTestCase):
	def test_users(self):
		login = self.client.login(username=self.normal_user.username,password='!')
		self.assertTrue(login)
		login = self.client.login(username=self.admin_user.username,password='!')
		self.assertTrue(login)


#### Testing the Views

# class TestStart(LinkTestCase):

# 	def test_start(self):  ## (0.323000s)
# 		response = self.client.get(reverse('training_start'))
# 		self.assertEqual(response.status_code, 200)

# 	def test_start_as_function(self): ## (0.062000s)
# 		request = RequestFactory().get(reverse('training_start'))
# 		request.user = AnonymousUser()
# #        request.user = User.objects.get(username='thomas6')
# 		request.session = {}
# 		response = StartView.as_view()(request)
# 		self.assertEqual(response.status_code, 200)


class TestVisitLinkView(LinkTestCase):

	def test_normal_operation(self):
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		login = self.client.login(username=self.admin_user.username,password='!')
		response = self.client.get(reverse('linkvisit', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, l.url ,target_status_code=302)

	def test_unauthenticated_user(self):
		## Same as normal operation
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		response = self.client.get(reverse('linkvisit', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, l.url ,target_status_code=302)

	def test_404(self):
		# Use validly formatted UUID that is not in the DB
		response = self.client.get(reverse('linkvisit', kwargs={'pk': '77f0ce70-d9fb-4086-a342-acfdfdcafe10'}))
		self.assertEqual(response.status_code, 404)

	def test_test_link(self):
		## Link is created with status = None, visit should run test_link which populates status
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkvisit', kwargs={'pk': l.pk}))
		l.refresh_from_db()
		self.assertIsNotNone(l.status)

	def test_test_link_unauthenticated(self):
		## Link is created with status = None, visit should run test_link which populates status
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		response = self.client.get(reverse('linkvisit', kwargs={'pk': l.pk}))
		l.refresh_from_db()
		self.assertIsNone(l.status)

	def test_test_link_not_owner(self):
		## Link is created with status = None, visit should run test_link which populates status
		l = LinkFactory.create(url=test_url,profile=self.normal2_pro,status=None)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkvisit', kwargs={'pk': l.pk}))
		l.refresh_from_db()
		self.assertIsNone(l.status)

class TestTestLinkView(LinkTestCase):

	def test_normal_operation(self):
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linktest', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 302)
		self.assertRedirects(response, l.get_absolute_url() ,target_status_code=200)
		l.refresh_from_db()
		self.assertIsNotNone(l.status)

	def test_unauthenticated_user(self):
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		response = self.client.get(reverse('linktest', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 302)
		redirect_url = '/login/?next=' + reverse('linktest', kwargs={'pk': l.pk})
		self.assertRedirects(response, redirect_url ,target_status_code=200)
		l.refresh_from_db()
		self.assertIsNone(l.status)

	def test_not_owner(self):
		l = LinkFactory.create(url=test_url,profile=self.normal2_pro,status=None)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linktest', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 404)
		l.refresh_from_db()
		self.assertIsNone(l.status)

class TestLinkDetail(LinkTestCase):

	def test_not_owner_public(self):
		l = LinkFactory.create(url=test_url,profile=self.normal2_pro,status=None,public=True)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkdetail', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 200)

	def test_not_found(self):
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkdetail', kwargs={'pk': '77f0ce70-d9fb-4086-a342-acfdfdcafe10'}))
		self.assertEqual(response.status_code, 404)

	def test_unauthenticated_user(self):
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		response = self.client.get(reverse('linkdetail', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 302)
		redirect_url = '/login/?next=' + reverse('linkdetail', kwargs={'pk': l.pk})
		self.assertRedirects(response, redirect_url ,target_status_code=200)

	def test_owner(self):
		l = LinkFactory.create(url=test_url,profile=self.normal_pro,status=None)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkdetail', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 200)

	def test_not_owner_private_link(self):
		l = LinkFactory.create(url=test_url,profile=self.normal2_pro,status=None,public=False)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkdetail', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 404)

	def test_not_owner_private_user(self):
		l = LinkFactory.create(url=test_url,profile=self.admin_pro,status=None,public=True)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkdetail', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 404)

class TestLinkCreate(LinkTestCase):

	def test_unauthenticated_user(self):
		response = self.client.get(reverse('linkcreate'))
		self.assertEqual(response.status_code, 302)
		redirect_url = '/login/?next=' + reverse('linkcreate')
		self.assertRedirects(response, redirect_url ,target_status_code=200)

	def test_successful_get(self):
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkcreate'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'links/link_form.html')

	def test_successful_copy_get(self):
		l = LinkFactory.create(url=test_url,profile=self.normal2_pro)
		login = self.client.login(username=self.normal_user.username,password='!')
		response = self.client.get(reverse('linkcopy', kwargs={'pk': l.pk}))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'links/link_form.html')

	def test_successful_post(self):
		login = self.client.login(username=self.normal_user.username,password='!')

		response = self.client.post(reverse('linkcreate'),
							 {'title': '',
							  'url': test_url,
							  'comment': '',
							  'public': '',
							  'tages': '',
							  })

		self.assertEqual(response.status_code, 302)
		self.assertEqual(response['Location'], reverse('linksentry'))

		l = Link.objects.get(url=test_url,profile=self.normal_pro)
		self.assertEqual(l.url, test_url)

	def test_unsuccessful_post(self):
		l = LinkFactory.create(url=test_url,profile=self.normal_pro)

		login = self.client.login(username=self.normal_user.username,password='!')

		response = self.client.post(reverse('linkcreate'),
							 {'title': '',
							  'url': test_url,
							  'comment': '',
							  'public': '',
							  'tags': '',
							  })

		self.assertEqual(response.status_code, 200)
		self.assertFormError(response, 'form', 'url', 'URL has already been saved')















