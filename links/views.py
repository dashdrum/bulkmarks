from datetime import datetime
import time

from django.shortcuts import render, get_object_or_404
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
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank

from braces.views import SuccessURLRedirectListMixin
from annoying.functions import get_object_or_None

from rest_framework import (viewsets, status)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, UpdateAPIView

from .serializers import LinkSerializer, AddURLLinkSerializer, TestLinkSerializer
from .models import Link, Profile, InterfaceFile
from .forms import (LinkForm, ImportFileForm, ExportFileForm, OtherUserInputForm, DeleteUserLinksInputForm,
                    SearchInputForm, )
from .utils import get_title, get_profile, test_link
from .choices import LINK_STATUS_CHOICES
from .tasks import (import_links_from_netscape, export_links_to_netscape, test_all_links, )

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

class LinkListView(FormMixin, ListView):
	model = Link
	ordering =  ['-created_on']
	paginate_by = 10
	paginator_class = PaginatorFive
	template_name = 'links/link_list.html'

	form_class = OtherUserInputForm
	search_form_class = SearchInputForm

	def get(self, request, *args, **kwargs):

		self.scope = kwargs.get('scope',None)

		if not request.user.is_authenticated and self.scope != 'public':
			return HttpResponseRedirect(reverse('links', kwargs={'scope': 'public'}))

		if self.scope == None:
			return HttpResponseRedirect(reverse('links', kwargs={'scope': 'user'}))

		return super(LinkListView, self).get(request, *args, **kwargs)

	def get_queryset(self):
		self.profile = None
		qs = Link.objects
		if self.scope == 'user':
			user = self.request.user
			self.profile = get_profile(user)
			qs = qs.filter(profile=self.profile)
		elif self.scope == 'public':
			qs = qs.filter(public=True)
		else:
			self.profile = get_object_or_None(Profile,user__username=self.scope)
			qs = qs.filter(profile=self.profile, public = True)
		self.queryset = qs
		return super(LinkListView,self).get_queryset()

	def get_context_data(self, **kwargs):

		context = super(LinkListView,self).get_context_data(**kwargs)
		context['latest_public'] = Link.objects.filter(public = True).order_by('-created_on')
		context['scope'] = self.scope
		context['searchform'] = self.search_form_class(initial= {'scope': self.scope})

		if self.profile:
			context['display_name'] = self.profile.display_name
			context['username'] = self.profile.user.username

		return context

	#=============================================================================#
	#
	#     Handle view user links
	#

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
		return reverse('links', kwargs={'scope': user.username})

class AllTagLinkListView(LinkListView):

	def get_queryset(self):
		self.profile = None
		tag = self.kwargs.get('tag',None)
		print('Tag:',tag)
		self.queryset = Link.objects.filter(tags__name__in=[tag],public=True)
		return ListView.get_queryset(self) ## Using the logic from the ListView class, not the direct ancestor
										   ## Yes, self is needed here

	def get_context_data(self, **kwargs):

		context = super(AllTagLinkListView,self).get_context_data(**kwargs)

		context['tag'] = self.kwargs.get('tag',None)

		return context


class UserTagLinkListView(AllTagLinkListView):

	def get_queryset(self):
		tag = self.kwargs.get('tag',None)
		user = self.request.user
		self.profile = get_profile(user)
		self.queryset = Link.objects.filter(tags__name__in=[tag],profile=self.profile)
		return ListView.get_queryset(self) ## Using the logic from the ListView class, not the direct ancestor
										   ## Yes, self is needed here


class OtherTagLinkListView(AllTagLinkListView):

	def get_queryset(self):
		tag = self.kwargs.get('tag',None)
		user = get_object_or_404(User,username = self.kwargs.get('username',None))
		self.profile = get_object_or_None(Profile,user=user)
		self.queryset = Link.objects.filter(tags__name__in=[tag],profile=self.profile,public=True)
		return ListView.get_queryset(self) ## Using the logic from the ListView class, not the direct ancestor
										   ## Yes, self is needed here


class LinkDetailView(LoginRequiredMixin,DetailView):
	model = Link

	def get_object(self, queryset=None):

		object = super(LinkDetailView,self).get_object(queryset)

		user = self.request.user

		if user == object.profile.user or object.public is True:
			return object

		raise Http404()


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
			form.save_m2m()
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

		raise Http404()


class LinkDeleteView(LoginRequiredMixin, SuccessURLRedirectListMixin, DeleteView):

	model=Link
	success_list_url = 'userlinks'

	def get_object(self, queryset=None):

		obj = super(LinkDeleteView,self).get_object(queryset)

		user = self.request.user

		if user == obj.profile.user:
			return obj

		raise Http404()

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
			raise Http404()

		return object

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linkdetail', kwargs={'pk': self.object.id})

	def get(self, request, *args, **kwargs):

		self.object = self.get_object()

		test_link(self.object.id)

		return HttpResponseRedirect(self.get_redirect_url(*args,**kwargs))

class TestAllLinksView(LoginRequiredMixin, RedirectView):

	def get(self, request, *args, **kwargs):

		profile = get_profile(self.request.user)

		test_all_links(profile.id)

		return super(TestAllLinksView, self).get(request, *args, **kwargs)

	def get_redirect_url(self, *args, **kwargs):

		return reverse('userlinks')

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

		if user == object.profile.user:
			test_link(object.id)

		if user == object.profile.user or object.public is True:
			return object

		raise Http404()

class DeleteUserLinksView(PermissionRequiredMixin,FormView):
	form_class = DeleteUserLinksInputForm
	template_name = "links/delete_user_links.html"
	permission_required = "links.delete_link"
	raise_exception = True

	def form_valid(self, form):
		self.user = form.cleaned_data.get('user_select',None)
		self.profile = get_profile(self.user)

		for l in Link.objects.filter(profile=self.profile):
			l.delete()

		return super(DeleteUserLinksView, self).form_valid(form)

	def get_success_url(self):
		return reverse('otherlinks', kwargs={'username': self.profile.user.username})




class SearchLinkListView(LoginRequiredMixin,FormMixin,ListView):
	model = Link
	ordering =  ['-created_on']
	paginate_by = 10
	paginator_class = PaginatorFive
	template_name = 'links/search_list.html'
	form_class = SearchInputForm

	def get(self, request, *args, **kwargs):
		self.scope = kwargs.get('scope',None)
		self.searchparam = kwargs.get('searchparam',None)

		return super(SearchLinkListView, self).get(request, *args, **kwargs)

	def get_queryset(self):
		qs = Link.search_objects.search(self.searchparam)
		if self.scope == 'user':
			user = self.request.user
			self.profile = get_profile(user)
			qs = qs.filter(profile=self.profile)
		elif self.scope == 'public':
			qs = qs.filter(public=True)
		else:
			self.profile = get_object_or_None(Profile,user__username=self.scope)
			qs = qs.filter(profile=self.profile, public = True)
		self.queryset = qs
		return self.queryset

	def get_context_data(self, **kwargs):

		context = super(SearchLinkListView,self).get_context_data(**kwargs)

		if self.scope != 'public':
			context['display_name'] = self.profile.display_name

		context['search_term'] = self.searchparam

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
		scope = self.request.POST.get('scope',None)
		searchparam = self.request.POST.get('searchparam',None)
		return reverse('search', kwargs={'scope': scope, 'searchparam': searchparam})

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
			raise Http404()

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
			form.save_m2m()
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



