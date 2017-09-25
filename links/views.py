from datetime import datetime
import time

from django.shortcuts import render
from django.views.generic import (FormView, TemplateView, ListView, CreateView,
									DetailView, UpdateView, RedirectView, DeleteView, )
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormMixin
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
from django.core.paginator import Page, Paginator

from braces.views import SuccessURLRedirectListMixin
from annoying.functions import get_object_or_None

from rest_framework import (viewsets, status)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, UpdateAPIView

from .serializers import LinkSerializer, AddURLLinkSerializer, TestLinkSerializer
from .models import Link, Profile, InterfaceFile
from .forms import LinkForm, ImportFileForm, ExportFileForm, UserInputForm
from .utils import get_title, get_profile, test_link
from .choices import LINK_STATUS_CHOICES
from .tasks import (import_links_from_netscape, export_links_to_netscape, )

class PageFive(Page):

	'''
		Include info for next 5 and previous 5 pages
	'''

	def has_next_five(self):
		return self.number < self.paginator.num_pages - 5

	def has_previous_five(self):
		return self.number > 6

	def next_five_page_number(self):
		return self.paginator.validate_number(self.number + 5)

	def previous_five_page_number(self):
		return self.paginator.validate_number(self.number - 5)

class PaginatorFive(Paginator):

	'''
		Uses the PageFive class to report info for next and
		previous 5 pages

		Set pageinator_class in ListView to use
	'''

	def _get_page(self, *args, **kwargs):
		"""
		Return an instance of a single page using the PageFive object
		"""
		return PageFive(*args, **kwargs)

class PublicLinkListView(ListView):
	model = Link
	ordering =  ['-created_on']
	paginate_by = 10
	paginator_class = PaginatorFive
	template_name = 'links/link_list.html'

	def get_queryset(self):
		self.queryset = Link.objects.filter(public=True)
		return super(PublicLinkListView,self).get_queryset()

	# def get_context_data(self, **kwargs):

	# 	context = super(PublicLinkListView,self).get_context_data(**kwargs)

	# 	return contexthttps://docs.djangoproject.com/en/1.11/ref/templates/builtins/#if


class UserLinkListView(LoginRequiredMixin, FormMixin, PublicLinkListView):

	form_class = UserInputForm

	def get_queryset(self):
		user = self.request.user
		self.profile = get_profile(user)
		self.queryset = Link.objects.filter(profile=self.profile)
		return ListView.get_queryset(self) ## Using the logic from the ListView class, not the direct ancestor
										   ## Yes, self is needed here

	def get_context_data(self, **kwargs):

		context = super(UserLinkListView,self).get_context_data(**kwargs)

		context['latest_public'] = Link.objects.filter(public = True).order_by('-created_on')

		context['display_name'] = self.profile.display_name

		return context

	def post(self, request, *args, **kwargs):
		"""
		Handles POST requests, instantiating a form instance with the passed
		POST variables and then checked for validity.
		"""
		form = self.get_form()
		self.form = form
		if form.is_valid():
			return self.form_valid(form)
		else:
			return self.form_invalid(form)

	def put(self, *args, **kwargs):
		return self.post(*args, **kwargs)

	def get_success_url(self):
		user = self.form.cleaned_data.get('user_select',None)
		profile = get_profile(user)
		print('PK:', profile.pk)
		return reverse('otherlinks', kwargs={'pk': profile.pk})


class OtherLinkListView(UserLinkListView):

	def get_queryset(self):
		user_pk = self.kwargs.get('pk',None)
		self.profile = get_object_or_None(Profile,pk=user_pk)
		self.queryset = Link.objects.filter(profile=self.profile,public=True)
		return ListView.get_queryset(self) ## Using the logic from the ListView class, not the direct ancestor
										   ## Yes, self is needed here

	def get_context_data(self, **kwargs):

		context = super(OtherLinkListView,self).get_context_data(**kwargs)

		context['other_list'] = True

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

		if instance.file_format == 'D' or instance.file_format == 'N': # Netscape Bookmark File (Used by Delicious)
			import_links_from_netscape(instance.id)
		else:
			instance.status = 'E' # Unknown file format
			instance.save()

		return super(UploadImportFileTemplateView,self).form_valid(form)

from django.core.files import File

class ExportLinksView(LoginRequiredMixin,FormView):

	form_class = ExportFileForm
	template_name = 'links/export.html'

	def get_context_data(self, **kwargs):
		context = super(ExportLinksView,self).get_context_data(**kwargs)

		profile = get_profile(self.request.user)

		context['filename'] = profile.user.username + datetime.now().strftime('-%Y-%m-%d') + '.html'

		return context

	def form_valid(self,form):

		profile = get_profile(self.request.user)

		export_id = export_links_to_netscape(get_profile(self.request.user).id)

		file_instance = get_object_or_None(InterfaceFile,id=export_id,profile=profile)

		# Create the HttpResponse object with the appropriate header.
		response = HttpResponse(file_instance.text,content_type='text/html')
		response['Content-Disposition'] = 'attachment; filename="' + file_instance.file_name + '"'

		return response

		# No super call needed

class TestLinkView(LoginRequiredMixin,SingleObjectMixin, RedirectView):

	''' test the link them redisplay details page '''

	model = Link

	def get_object(self, queryset=None):

		object = super(TestLinkView,self).get_object(queryset)

		user = self.request.user

		if user != object.profile.user:
			return HttpResponseForbidden()

		return object

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linkdetail', kwargs={'pk': self.object.id})

	def get(self, request, *args, **kwargs):

		self.object = self.get_object()

		test_link(self.object.id)

		return HttpResponseRedirect(self.get_redirect_url(*args,**kwargs))

class VisitLinkView(SingleObjectMixin, RedirectView):

	model = Link

	def get(self, request, *args, **kwargs):

		self.object = self.get_object()

		if self.object:
			url = self.get_redirect_url(*args, **kwargs)

			if url:
				return HttpResponseRedirect(url)
			else:
				return HttpResponseGone()
		else:
			return HttpResponseForbidden()

	def get_redirect_url(self, *args, **kwargs):

		return self.object.url

	def get_object(self, queryset=None):

		object = super(VisitLinkView,self).get_object(queryset)

		user = self.request.user

		print('User:', user)

		if user == object.profile.user:
			test_link(object.id)

		if user == object.profile.user or object.public is True:
			return object

		return None

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



