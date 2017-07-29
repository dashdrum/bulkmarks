from datetime import datetime
import time

from django.shortcuts import render
from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView, DeleteView)
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.http import (HttpResponseRedirect, Http404, HttpResponse, HttpResponseForbidden, HttpResponseGone)
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from braces.views import SuccessURLRedirectListMixin
from annoying.functions import get_object_or_None
from django.utils.timezone import make_aware, utc
from braces.views import SuccessURLRedirectListMixin

from .models import Link, Profile, InterfaceFile
from .forms import LinkForm, ImportFileForm, ExportFileForm

def get_profile(user):
	try:
		profile = Profile.objects.get(user = user)
		return profile
	except:
		profile = Profile(user=user,display_name=user.username,email=user.email)
		return profile

class UserLinkListView(LoginRequiredMixin,ListView):
	model = Link
	ordering =  ['-created_on']
	paginate_by = 12

	def get_queryset(self):
		user = self.request.user
		#print('User:', user)
		profile = get_profile(user)
		self.queryset = Link.objects.filter(profile=profile)
		return super(UserLinkListView,self).get_queryset()


class LinkDetailView(LoginRequiredMixin,DetailView):
	model = Link

	def get_object(self, queryset=None):

		object = super(LinkDetailView,self).get_object(queryset)

		user = self.request.user

		if user == object.profile.user or object.public is True:
			return object

		return HttpResponseForbidden()


class LinkCreateView(LoginRequiredMixin,CreateView):
	model = Link
	form_class = LinkForm

	def get_success_url(self):
		return reverse('userlinks')

	def form_valid(self, form):
		user = User.objects.get(username = 'dgentry')
		profile = Profile.objects.get(user = user)
		self.object = form.save(commit=False)
		self.object.profile = profile
		self.object.save()
		return HttpResponseRedirect(self.get_success_url())


class LinkUpdateView(LoginRequiredMixin,UpdateView):
	model = Link
	form_class = LinkForm

	def get_success_url(self):
		return reverse('linkdetail', kwargs={'pk': self.object.id})

	def get_object(self, queryset=None):

		obj = super(LinkUpdateView,self).get_object(queryset)

		user = self.request.user

		if user == obj.profile.user:
			return obj

		return HttpResponseForbidden()


class LinkDeleteView(PermissionRequiredMixin, SuccessURLRedirectListMixin, DeleteView):

	permission_required = "links.delete_link"
	raise_exception = True
	model=Link
	success_list_url = 'userlinks'

class UploadImportFileTemplateView(LoginRequiredMixin,FormView):

	form_class = ImportFileForm
	template_name = 'links/import.html'

	def get_success_url(self):
		return reverse('userlinks')

	def form_valid(self,form):

		user = self.request.user

		instance = InterfaceFile()
		instance.profile = get_profile(user)
		instance.file_format = form.cleaned_data['import_type']
		instance.file_type = 'I'  ## This is an import file

		f = self.request.FILES['import_file']
		instance.file_name = f.name
		if not f.multiple_chunks():  # enforce size limit
			instance.text = f.read()
		else:
			instance.status = 'E'

		instance.save()
		instance.refresh_from_db()

		import_links_from_file(instance.id)

		return super(UploadImportFileTemplateView,self).form_valid(form)

from django.core.files import File

class ExportLinksView(LoginRequiredMixin,FormView):

	form_class = ExportFileForm
	template_name = 'links/export.html'

	def form_valid(self,form):

		profile = get_profile(self.request.user)

		export_id = export_links_to_delicious(get_profile(self.request.user).id)

		file_instance = get_object_or_None(InterfaceFile,id=export_id,profile=profile)

		# Create the HttpResponse object with the appropriate header.
		response = HttpResponse(file_instance.text,content_type='text/html')
		response['Content-Disposition'] = 'attachment; filename="' + file_instance.file_name + '"'

		return response

		# No super call needed

class TestLinkView(LoginRequiredMixin,DetailView):
	model = Link
	template_name = 'links/link_test_detail.html'

	def get_object(self, queryset=None):

		object = super(TestLinkView,self).get_object(queryset)

		user = self.request.user

		if user != object.profile.user:
			return HttpResponseForbidden()

		return object

	def get_context_data(self, **kwargs):
		context = super(TestLinkView,self).get_context_data(**kwargs)

		context['link_status_code'] = test_link(self.object.id)

		return context

class VisitLinkView(LoginRequiredMixin, SingleObjectMixin, RedirectView):

	model = Link

	def get(self, request, *args, **kwargs):

		self.object = self.get_object()

		test_link(self.object.id)

		url = self.get_redirect_url(*args, **kwargs)

		if url:
			return HttpResponseRedirect(url)
		else:
			return HttpResponseGone()

	def get_redirect_url(self, *args, **kwargs):

		return self.object.url

	def get_object(self, queryset=None):

		object = super(VisitLinkView,self).get_object(queryset)

		user = self.request.user

		if user == object.profile.user or object.public is True:
			return object

		return HttpResponseForbidden()

#-----------------------------------------------------------------------------#

from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import datetime

def import_links_from_file(import_file_id):

	class MyHTMLParser(HTMLParser):

		current_tag = None
		current_link = None

		def handle_starttag(self, tag, attrs):

			self.current_tag = tag

			if tag == 'dt':
				if self.current_link:
					self.current_link.save()
				self.current_link = Link()
				self.current_link.profile = profile
			elif tag == 'a':
				attr_dict = dict(attrs)
				self.current_link.url = attr_dict.get('href',None)
				self.current_link.public = not bool(int(attr_dict['private']))
				self.current_link.created_on = make_aware(datetime.utcfromtimestamp(float(attr_dict['add_date'])))
				# self.current_link.tags = attr_dict['tags']
			elif tag == 'dd':
				None

		def handle_endtag(self,tag):
			if tag == 'dl':
				self.current_link.save()

		def handle_data(self, data):
			if data != '\n':
				if self.current_tag == 'a':
					self.current_link.title = data
				elif self.current_tag == 'dd':
					self.current_link.comment = data

	import_status = None

	try:
		import_obj = get_object_or_None(InterfaceFile, id = import_file_id)
		profile = import_obj.profile
	except:
		# raise some sort of error
		import_status = 'E'

	parser = MyHTMLParser()

	if not import_status:
		try:
			parser.feed(import_obj.import_text)
			import_status = 'Y'
		except:
			import_status = 'E'

	import_obj.status = import_status
	import_obj.save()

	return import_status

#-----------------------------------------------------------------------------#

def test_link(link_id):

	def convert_link_status(status_code):

		if status_code[0:1] == '403':
			return 'F'
		elif status_code[0:1] == '4':
			return 'N'
		elif status_code[0:1] == '3':
			return 'R'
		elif status_code[0:1] == '2':
			return 'O'
		else:
			return 'E'

	l = get_object_or_None(Link, id = link_id)
	if l is not None:
		try:
			status_code = get_link_status(l.url)
			if status_code is not None:
				l.status = convert_link_status(str(status_code))
				l.tested_on = datetime.now(utc)
				l.save()
				return l.status
		except:
			l.status = 'E'
			l.tested_on = datetime.now(utc)
			l.save()
	return None


from http.client import HTTPSConnection, HTTPConnection
import socket

def get_link_status(url):
	"""
	Gets the HTTP status of the url
	"""
	https=False
	#url=re.sub(r'(.*)#.*$',r'\1',url)
	url=url.split('/',3)
	if len(url) > 3:
		path='/'+url[3]
	else:
		path='/'
	if url[0] == 'http:':
		port=80
	elif url[0] == 'https:':
		port=443
		https=True
	if ':' in url[2]:
		host=url[2].split(':')[0]
		port=url[2].split(':')[1]
	else:
		host=url[2]
	try:
		headers={'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0',
				 'Host':host}
		if https:
			conn=HTTPSConnection(host=host,port=port,timeout=10)
		else:
			conn=HTTPConnection(host=host,port=port,timeout=10)
		conn.request(method="HEAD",url=path,headers=headers)
		response=str(conn.getresponse().status)
		conn.close()
		return response
	except:
		pass

	## something failed
	return '500'




#-----------------------------------------------------------------------------#


def export_links_to_delicious(profile_id):

	''' Writes link information to an HTML file using the horrible del.icio.us format '''

	profile = get_object_or_None(Profile,id=profile_id)

	queryset = Link.objects.filter(profile=profile).order_by('-created_on')

	filename = profile.user.username + '.html'

	instance = InterfaceFile()
	instance.profile = profile
	instance.file_format = 'D'
	instance.file_type = 'E'  ## This is an export file
	instance.file_name = filename

	outtext = ''   ## Holds the text of the file

	# Write header info

	outtext += '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n'
	outtext += '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
	outtext += '<TITLE>Bookmarks</TITLE>\n'
	outtext += '<H1>Bookmarks</H1>\n'
	outtext += '<DL><p>\n'

	# Process links

	for link in queryset:
		outtext += '<DT><A HREF="'
		outtext += link.url
		outtext += '" ADD_DATE="'
		outtext += str(time.mktime(link.created_on.timetuple()))
		outtext += '" PRIVATE="'
		outtext += str(int(not link.public)) #AWKWARD!
		outtext += '" TAGS="'
		outtext += ''
		outtext += '">'
		outtext += link.title
		outtext += '</A>\n'

		if link.comment:
			outtext += '<DD>'
			outtext += link.comment + '\n'

	# Write footer info

	outtext += '</DL><p>'

	instance.text = outtext

	instance.save()

	return instance.id

