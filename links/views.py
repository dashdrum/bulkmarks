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
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import make_aware, utc
from django.utils.html import escape
from django.db import IntegrityError
from django.db import transaction
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank

from braces.views import SuccessURLRedirectListMixin
from annoying.functions import get_object_or_None

from rest_framework import (viewsets, status)
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, UpdateAPIView

from .models import Link, InterfaceFile
from profiles.models import  Profile
from .forms import (LinkForm, ImportFileForm, ExportFileForm, OtherUserInputForm, DeleteUserLinksInputForm,
					SearchInputForm, TagInputForm,  )
from .utils import test_link
from profiles.utils import get_profile
from .link_utils import get_title
from .choices import LINK_STATUS_CHOICES
from .tasks import (import_links_from_netscape, export_links_to_netscape, test_all_links, delete_user_links )
from .messages import messages
from .serializers import LinkSerializer, AddURLLinkSerializer, TestLinkSerializer
from profiles.views import ProfileContext

class LinkListView(ProfileContext, FormMixin, ListView):
	model = Link
	ordering =  ['-created_on']
	paginate_by = 20
	template_name = 'links/link_list.html'

	form_class = OtherUserInputForm
	search_form_class = SearchInputForm
	tag_form_class = TagInputForm
	user_form_class = OtherUserInputForm

	def get(self, request, *args, **kwargs):

		self.scope = kwargs.get('scope',None)

		if not request.user.is_authenticated and self.scope != 'public':
			# return HttpResponseRedirect(reverse('links', kwargs={'scope': 'public'}))
			self.scope = 'public'

		if self.scope == None:
			# return HttpResponseRedirect(reverse('links', kwargs={'scope': 'user'}))
			self.scope = 'user'

		self.mid = self.request.GET.get('mid',None)

		return super(LinkListView, self).get(request, *args, **kwargs)

	def add_scope(self,qs):
		if self.scope == 'user':
			user = self.request.user
			self.profile = get_profile(user)
			qs = qs.filter(profile=self.profile)
		elif self.scope == 'public':
			qs = qs.filter(public=True, profile__acct_public = True)
		else:
			self.profile = get_object_or_None(Profile,user__username=self.scope)
			if self.profile:
				if self.request.user.is_superuser:
					qs = qs.filter(profile=self.profile)
				elif self.profile.acct_public is False:
					raise Http404
				else:
					qs = qs.filter(profile=self.profile, public = True)
			else:
				raise Http404
		return qs

	def get_queryset(self):
		self.profile = None
		qs = self.add_scope(Link.objects)
		qs = qs.select_related('profile').prefetch_related('profile__user')
		self.queryset = qs
		return super(LinkListView,self).get_queryset()

	def get_context_data(self, **kwargs):

		context = super(LinkListView,self).get_context_data(**kwargs)
		context['latest_public'] = Link.objects.filter(public = True, profile__acct_public = True).order_by('-created_on')
		context['scope'] = self.scope
		context['searchform'] = self.search_form_class(initial= {'scope': self.scope})
		context['tagform'] = self.tag_form_class(initial= {'scope': self.scope})
		context['userform'] = self.user_form_class()

		if self.profile:
			context['display_name'] = self.profile.display_name
			context['username'] = self.profile.user.username

		if self.mid:
			try:
				context['message'] = messages[self.mid]
			except KeyError:
				pass   # ignore an unknown key


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
		return reverse('links', kwargs={'scope': user.username})

class TagLinkListView(LoginRequiredMixin,LinkListView):

	form_class = TagInputForm

	def get_queryset(self):
		qs = super(TagLinkListView,self).get_queryset()
		tag = self.kwargs.get('tag',None)
		self.queryset = qs.filter(tags__name__in=[tag],public=True, profile__acct_public = True)
		return self.queryset

	def get_context_data(self, **kwargs):

		context = super(TagLinkListView,self).get_context_data(**kwargs)

		context['tag'] = self.kwargs.get('tag',None)

		return context

	#=============================================================================#
	#
	#     Handle tag search
	#

	def get_success_url(self):
		scope = self.form.cleaned_data.get('scope',None)
		searchtag = self.form.cleaned_data.get('searchtag',None)
		return reverse('taglinks', kwargs={'scope': scope, 'tag': searchtag})


class LinkDetailView(LoginRequiredMixin, ProfileContext, DetailView):
	model = Link

	def get_object(self, queryset=None):

		object = super(LinkDetailView,self).get_object(queryset)

		user = self.request.user

		if user == object.profile.user or (object.public is True and object.profile.acct_public is True):
			return object

		raise Http404()


class SendProfileToForm(object):
	''' Mixin to add the current user profile to the form parameters '''

	def get_form(self, form_class=None):

		if form_class is None:
			form_class = self.get_form_class()
		return form_class(**self.get_form_kwargs(),current_user_profile=get_profile(self.request.user))


class LinkCreateView(LoginRequiredMixin, SendProfileToForm, ProfileContext, CreateView):
	model = Link
	form_class = LinkForm

	def tags_as_string(self,tags):
		""" Return tag names in a comma-delimited string """
		names = []
		for name in tags.names():
			if ',' in name or ' ' in name:
				names.append('"%s"' % name)
			else:
				names.append(name)
		return ', '.join(sorted(names))

	def get_initial(self):
		self.initial = {}  ## Don't know why I have to do this. Old data was hanging around
		pk = self.kwargs.get('pk',None)
		if pk:
			add_link = get_object_or_404(Link,pk=pk)
			self.initial['id'] = add_link.id
			self.initial['title'] = add_link.title
			self.initial['url'] = add_link.url
			self.initial['comment'] = add_link.comment
			self.initial['tags'] = self.tags_as_string(add_link.tags)

		user = self.request.user
		profile = get_profile(user)

		self.initial['profile'] = profile

		return super(LinkCreateView,self).get_initial()

	def get_success_url(self):
		return reverse('linksentry')

class LinkUpdateView(LoginRequiredMixin, SendProfileToForm, ProfileContext, UpdateView):
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


class LinkDeleteView(LoginRequiredMixin, ProfileContext, SuccessURLRedirectListMixin, DeleteView):

	model=Link
	success_list_url = 'linksentry'

	def get_object(self, queryset=None):

		obj = super(LinkDeleteView,self).get_object(queryset)

		user = self.request.user

		if user == obj.profile.user:
			return obj

		raise Http404()

class UploadImportFileTemplateView(LoginRequiredMixin, ProfileContext, FormView):

	form_class = ImportFileForm
	template_name = 'links/import.html'

	def get_success_url(self):
		return reverse('linksentry') + '?mid=IMPORTSTART'

	def form_valid(self,form):

		user = self.request.user

		instance = InterfaceFile()
		instance.profile = get_profile(user)
		instance.file_format = form.cleaned_data['import_format']
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
			if settings.USE_CELERY:
				import_links_from_netscape.delay(instance.id)
			else:
				import_links_from_netscape(instance.id)
		else:
			# Form should catch this error.  How to report?
			instance.status = 'E' # Unknown file format
			instance.save()

		return super(UploadImportFileTemplateView,self).form_valid(form)

from django.core.files import File

class ExportLinksView(LoginRequiredMixin, ProfileContext, FormView):

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

class TestLinkView(LoginRequiredMixin, ProfileContext, SingleObjectMixin, RedirectView):

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

class TestAllLinksView(LoginRequiredMixin, ProfileContext, RedirectView):

	def get(self, request, *args, **kwargs):

		profile = get_profile(self.request.user)

		if settings.USE_CELERY:
			test_all_links.delay(profile.id)
		else:
			test_all_links(profile.id)

		return super(TestAllLinksView, self).get(request, *args, **kwargs)

	def get_redirect_url(self, *args, **kwargs):

		return reverse('linksentry') + '?mid=TESTSTART'

class VisitLinkView(SingleObjectMixin, ProfileContext, RedirectView):

	model = Link

	def get(self, request, *args, **kwargs):

		self.object = self.get_object()

		if self.object:
			url = self.get_redirect_url(*args, **kwargs)

			if url:
				return HttpResponseRedirect(url)
			else:
				return HttpResponseGone()    ## Never
		else:
			return HttpResponseForbidden()   ## Never

	def get_redirect_url(self, *args, **kwargs):

		return self.object.url

	def get_object(self, queryset=None):

		object = super(VisitLinkView,self).get_object(queryset)

		user = self.request.user

		if user == object.profile.user:
			test_link(object.id)

		if user == object.profile.user or (object.public is True and object.profile.acct_public is True):
			return object

		raise Http404()

class DeleteUserLinksView(PermissionRequiredMixin, ProfileContext, FormView):
	form_class = DeleteUserLinksInputForm
	template_name = "links/delete_user_links.html"
	permission_required = "links.delete_link"
	raise_exception = True

	def form_valid(self, form):
		self.user = form.cleaned_data.get('user_select',None)
		self.profile = get_profile(self.user)

		if settings.USE_CELERY:
			delete_user_links.delay(self.profile.id)
		else:
			delete_user_links(self.profile.id)

		return super(DeleteUserLinksView, self).form_valid(form)

	def get_success_url(self):
		return reverse('links', kwargs={'scope': self.profile.user.username})  + '?mid=DELETEUSERLINKS'




class SearchLinkListView(LoginRequiredMixin,LinkListView):
	form_class = SearchInputForm

	def get(self, request, *args, **kwargs):
		self.scope = kwargs.get('scope',None)
		self.searchparam = kwargs.get('searchparam',None)

		return super(SearchLinkListView, self).get(request, *args, **kwargs)

	def get_queryset(self):
		self.profile = None
		if self.searchparam:
			qs = self.add_scope(Link.search_objects.search(self.searchparam))
		else:
			qs = self.add_scope(Link.objects.none())
		qs = qs.select_related('profile').prefetch_related('profile__user')
		self.queryset = qs
		return super(LinkListView,self).get_queryset() # Super of LinkListView, not current class

	def get_context_data(self, **kwargs):

		context = super(SearchLinkListView,self).get_context_data(**kwargs)

		context['search_term'] = self.searchparam

		return context

	#=============================================================================#
	#
	#     Handle search input
	#

	def get_success_url(self):
		scope = self.form.cleaned_data.get('scope',None)
		searchparam = self.form.cleaned_data.get('searchparam',None)
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
	serializer_class = LinkSerializer
	authentication_classes = []

	# 	## Test with: curl -v --data-ascii url="http://nmc.edu" http://localhost:8000/l/api/addurl/

class AddURLViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = Link.objects.all().order_by('-created_on')
	serializer_class = LinkSerializer

	# ## Test with: curl -v --data-ascii "url=https://my.nmc.edu&title=My NMC" http://localhost:8000/l/api/links/



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



