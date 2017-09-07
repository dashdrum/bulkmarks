from datetime import datetime
import time

from django.shortcuts import render
from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView, DeleteView)
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import PermissionRequiredMixin,LoginRequiredMixin
from django.http import (HttpResponseRedirect, Http404, HttpResponse, HttpResponseForbidden, HttpResponseGone,
						 HttpResponseBadRequest)
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import make_aware, utc
from django.utils.html import escape
from django.db import IntegrityError

from braces.views import SuccessURLRedirectListMixin
from annoying.functions import get_object_or_None

from rest_framework import (viewsets, status)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, UpdateAPIView

from .serializers import LinkSerializer, AddURLLinkSerializer, TestLinkSerializer
from .models import Link, Profile, InterfaceFile
from .forms import LinkForm, ImportFileForm, ExportFileForm
from .utils import get_title, get_profile, test_link
from .choices import LINK_STATUS_CHOICES

class UserLinkListView(LoginRequiredMixin,ListView):
	model = Link
	ordering =  ['-created_on']
	paginate_by = 12

	def get_queryset(self):
		user = self.request.user
		#print('User:', user)
		self.profile = get_profile(user)
		self.queryset = Link.objects.filter(profile=self.profile)
		return super(UserLinkListView,self).get_queryset()

	def get_context_data(self, **kwargs):

		context = super(UserLinkListView,self).get_context_data(**kwargs)

		context['display_name'] = self.profile.display_name

		return context


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
		user = self.request.user
		profile = get_profile(user)
		try:
			# Save object and show success
			self.object = form.save(commit=False)
			self.object.profile = profile
			self.object.save()
			return HttpResponseRedirect(self.get_success_url())
		except IntegrityError as e:
			# Add the error to the form and send it back
			form.add_error('url','URL has already been saved')
			return self.render_to_response(self.get_context_data(form=form))


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

		link_status = test_link(self.object.id)
		try:
			context['link_status_code'] = dict(LINK_STATUS_CHOICES)[link_status]
		except KeyError:
			context['link_status_code'] = link_status

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
					self.current_link.title = data[:200]
				elif self.current_tag == 'dd':
					self.current_link.comment = data

	import_status = None

	try:
		import_obj = get_object_or_None(InterfaceFile, id = import_file_id)
		print('Import file:', import_obj)
		profile = import_obj.profile
		print('Profile:', profile)
	except:
		# raise some sort of error
		print('get error')
		import_status = 'E'

	parser = MyHTMLParser()

	if not import_status:
		try:
			parser.feed(import_obj.text)
			import_status = 'Y'
		except:
			print('parser error')
			import_status = 'E'

	import_obj.status = import_status
	import_obj.save()

	return import_status




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

###############################################################################
#																			  #
#  A P I 																	  #
#																			  #
###############################################################################

class ProfileCheckMixin(object):

	def get_object(self):

		obj = super(ProfileCheckMixin,self).get_object()

		user = self.request.user
		user = User.objects.get(username='dgentry') ## Temp user assignment

		if user != obj.profile.user:
			return HttpResponseForbidden()

		return obj


class GetTitleAPIView(APIView):

	''' Return the title from a URL '''

	queryset = Link.objects.all() ## Needs a queryset for permissions to work

	def get(self, request, *args, **kwargs):

		url = request.GET.get('URL',None)

		error_code = None

		if not url: ## Something is missing
			return Response(status=status.HTTP_400_BAD_REQUEST,
							data={"error_code": '400', "error_message": 'Missing URL'})

		title, error_code = get_title(url)

		if not title: ## no title returned
			return Response(status=error_code,
							data={'error_code': error_code, 'error_message': 'No title returned'})

		return Response(status=status.HTTP_200_OK, data={"title": title})

class AddURLAPIView(CreateAPIView):

	''' Creates a new link row with the given URL '''

	queryset = Link.objects.all()
	serializer_class = AddURLLinkSerializer
	# permission_classes = (IsAuthenticated,)

	# 	## Test with: curl -v --data-ascii url="http://nmc.edu" http://localhost:8000/l/api/addurl/



class TestLinkAPIView(ProfileCheckMixin,UpdateAPIView):

	''' Tests the URL '''

	## AssertionError: Expected view TestLinkAPIView to be called with a URL keyword argument named "id". Fix your URL conf, or set the `.lookup_field` attribute on the view correctly.

	queryset = Link.objects.all()
	serializer = TestLinkSerializer
	lookup_field = 'id'

	## Test with: curl --header "Content-Type:application/json" --header "Accept: application/json" --request PATCH --data '{"id":"830fb618-d401-4b9a-9d0e-f238d8dd31b0"}' http://localhost:8000/l/api/testlink/
	##  (replace with desired ID)


###############################################################################
#																			  #
#  Modal dialogs         													  #
#																			  #
###############################################################################

from django.http import JsonResponse
from django.template.loader import render_to_string

def link_create(request):
	data = dict()

	if request.method == 'POST':
		form = LinkForm(request.POST)
		user = request.user
		profile = get_profile(user)
		if form.is_valid():
			object = form.save(commit=False)
			object.profile = profile
			object.save()
			data['form_is_valid'] = True
		else:
			data['form_is_valid'] = False
	else:
		form = LinkForm()

	context = {'form': form}
	data['html_form'] = render_to_string('links/includes/partial_link_create.html',
		context,
		request=request,
	)
	return JsonResponse(data)



