from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import datetime, timezone
import time
from django.utils.timezone import make_aware, utc
from annoying.functions import get_object_or_None
from bs4 import BeautifulSoup
from django.db import IntegrityError, DataError

from .models import InterfaceFile, Link, Profile


#-----------------------------------------------------------------------------#

def import_links_from_netscape(import_file_id):

	import_status = None

	try:
		import_obj = get_object_or_None(InterfaceFile, id = import_file_id)
		print('Import file:', import_obj)
		profile = import_obj.profile
	except:
		print('get error')
		raise

	soup = BeautifulSoup(import_obj.text, "html5lib")

	for link in soup.find_all('a'):
		bookmark = {}

		# url and title
		bookmark['url'] = link.get('href')

		if bookmark['url'][:bookmark['url'].index(':')] in ('javascript','place','file'):
			print('Skipping ', bookmark['url'][:bookmark['url'].index(':')])
			continue

		bookmark['title'] = link.string.strip()[:200] if link.string else bookmark['url']

		# add date
		secs = link.get('add_date')
		date = datetime.fromtimestamp(int(secs), tz=timezone.utc)
		bookmark['add_date'] = date

		# last modified
		secs = link.get('last_modified')
		if secs:
			date = datetime.fromtimestamp(int(secs), tz=timezone.utc)
			bookmark['last_modified'] = date

		# tags
		tags = link.get('tags')
		bookmark['tags'] = tags.split(',') if tags else []

		# comment
		sibling = link.parent.next_sibling
		bookmark['comment'] = sibling.string.strip()[:1000] if sibling and sibling.name == 'dd' else ''

		current_link = Link()
		current_link.profile = profile
		current_link.url = bookmark['url']
		current_link.title = bookmark['title']
		current_link.created_on = bookmark['add_date']
		current_link.comment = bookmark['comment']

		try:
			current_link.save()
		except IntegrityError: # duplicate entries
			print( 'Integrity Error on: ', bookmark)
		except DataError: # crazy data
			print( 'Data Error on: ', bookmark)

	return 'Y'

#-----------------------------------------------------------------------------#




def export_links_to_netscape(profile_id):

	''' Writes link information to an HTML file using the Netscape Bookmark format '''

	profile = get_object_or_None(Profile,id=profile_id)

	queryset = Link.objects.filter(profile=profile).order_by('-created_on')

	filename = profile.user.username + datetime.now().strftime('-%Y-%m-%d') + '.html'
	print('filename: ', filename)

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
		outtext += "%9.0f" % time.mktime(link.created_on.timetuple())
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