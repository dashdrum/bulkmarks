from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import datetime, timezone
from django.utils.timezone import make_aware, utc
from annoying.functions import get_object_or_None
from bs4 import BeautifulSoup
from django.db import IntegrityError, DataError

from .models import InterfaceFile, Link, Profile

def import_links_from_delicious(import_file_id):

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
		print('get error')
		raise

	parser = MyHTMLParser()

	if not import_status:
		try:
			parser.feed(import_obj.text)
			import_status = 'Y'
		except:
			print('parser error')
			raise

	import_obj.status = import_status
	import_obj.save()

	return import_status




#-----------------------------------------------------------------------------#

def import_links_from_netscape(import_file_id):

	import_status = None

	try:
		import_obj = get_object_or_None(InterfaceFile, id = import_file_id)
		print('Import file:', import_obj)
		profile = import_obj.profile
		print('Profile:', profile)
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

		bookmark['title'] = link.string.strip() if link.string else bookmark['url']

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


