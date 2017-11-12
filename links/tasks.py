from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import datetime, timezone
import time
from django.utils.timezone import make_aware, utc
from annoying.functions import get_object_or_None
from bs4 import BeautifulSoup
from django.db import IntegrityError, DataError
from django.core.mail import send_mail

from bulk.celery import app


from .models import InterfaceFile, Link, Profile
from .utils import test_link



#-----------------------------------------------------------------------------#

@app.task()
def import_links_from_netscape(import_file_id):

	import_obj = None

	import_status = None
	error_count = 0
	dupe_count = 0
	success_count = 0
	file_error = False

	try:
		import_obj = get_object_or_None(InterfaceFile, id = import_file_id)
		print('Import file:', import_obj)
		profile = import_obj.profile
	except:
		print('get import file error')
		file_error = True
		raise

	if import_obj:

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

			# public

			bookmark['public'] = True
			pub = link.get('private')
			if pub:
				if pub == "0":
					bookmark['public'] = True
				else:
					bookmark['public'] = False

			# tags
			bookmark['tags'] = []
			tags = link.get('tags')
			if tags:
				bookmark['tags'] = tags.split(',')

			# comment
			sibling = link.parent.next_sibling
			bookmark['comment'] = sibling.string.strip()[:1000] if sibling and sibling.name == 'dd' else ''

			current_link = Link()
			current_link.profile = profile
			current_link.url = bookmark['url']
			current_link.title = bookmark['title']
			current_link.created_on = bookmark['add_date']
			current_link.public = bookmark['public']
			current_link.comment = bookmark['comment']

			try:
				current_link.save()
				for t in  bookmark['tags']:
					current_link.tags.add(t)
				success_count += 1
			except IntegrityError: # duplicate entries
				print( 'Integrity Error on: ', bookmark)
				dupe_count += 1
			except DataError: # crazy data
				print( 'Data Error on: ', bookmark)
				error_count += 1

	print('File Error:', file_error)
	print('Success Count:', success_count)
	print('Dupe Count:', dupe_count)
	print('Error Count:', error_count)

	if file_error is False:
		import_status = 'Y'
	else:
		import_status = 'E'

	if import_obj:
		import_obj.status = import_status
		import_obj.save()
		send_import_email(import_obj,file_error, success_count, dupe_count, error_count)

	return import_status

def send_import_email(import_obj,file_error, success_count, dupe_count, error_count):

	sender = 'infobot@bulkmarks.com'
	subject = 'BULKmarks Import Results'
	recipients = [import_obj.profile.user.email]

	if file_error:
		message = 'Your file was not imported. Please check your input and try again.'
	else:
		message = 'Good news! \n\nYour file has been imported into your BULKmarks account.'
		message += '\n\n %d links were imported successfully.' % success_count
		message += '\n %d links were duplicates of those already saved by you and were not imported.' % dupe_count
		message += '\n %d links were rejected because of a format or data error.' % error_count
		message += '\n\n Thanks for using BULKmarks!'

	if recipients:
		print('Sending email',subject, message, sender, recipients)
		send_mail(subject, message, sender, recipients)

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
		outtext += ', '.join('{0}'.format(t) for t in link.tags.names())
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

#-----------------------------------------------------------------------------#



@app.task()
def test_all_links(profile_id):

	ok_count = 0
	redirect_count = 0
	error_count = 0
	not_found_count = 0

	profile = get_object_or_None(Profile,id=profile_id)

	queryset = Link.objects.filter(profile=profile)

	for link in queryset:

		status = test_link(link.id)

		if status == 'O':
			ok_count += 1
		elif status == 'N':
			not_found_count += 1
		elif status == 'E':
			error_count += 1
		elif status == 'R':
			redirect_count += 1

		# print('Status:', status, 'Title:', link.title[:20])

	print('OK Count:', ok_count)
	print('Redirect Count:', redirect_count)
	print('Not Found Count:', not_found_count)
	print('Error Count:', error_count)

	send_testall_email(profile,ok_count, not_found_count, redirect_count, error_count)

def send_testall_email(profile,ok_count, not_found_count, redirect_count, error_count):

	sender = 'infobot@bulkmarks.com'
	subject = 'BULKmarks Links Test Results'
	recipients = [profile.user.email]

	message = 'Whew! \n\nAll of the links in your BULKmarks account have been tested.'
	message += '\n\n %d links testd OK.' % ok_count
	message += '\n %d links redirected to another URL.' % redirect_count
	message += '\n %d links were not found.' % not_found_count
	message += '\n %d links returned an error.' % error_count
	message += '\n\n Thanks for using BULKmarks!'

	if recipients:
		print('Sending email',subject, message, sender, recipients)
		send_mail(subject, message, sender, recipients)

#-----------------------------------------------------------------------------#

@app.task()
def delete_user_links(profile_id):

	delete_count = 0

	profile = get_object_or_None(Profile,id=profile_id)

	for l in Link.objects.filter(profile=profile):
		l.delete()
		delete_count += 1

	print('Delete Count:', delete_count)


