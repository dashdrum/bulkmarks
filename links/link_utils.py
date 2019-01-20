from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError, ContentTooShortError
from http.client import RemoteDisconnected

import extruct
import requests
from w3lib.html import get_base_url

from bs4 import BeautifulSoup
from annoying.functions import get_object_or_None

def get_title(url):
	error_code = None
	title = None

	title, error_code = get_opengraph_title(url)
	print('og:title:', title, error_code)

	if not title:
		title, error_code = get_json_ld_headline(url)
		print('jl title:', title, error_code)

	if not title:
		title, error_code = get_html_title(url)
		print('html title:', title, error_code)

	return title, error_code


def get_html_title(url):
	error_code = None
	title = None

	try:
		## Need to change the agent to fool sites that want to block python bots
		## (Should be harder than this to fool someone)
		page = urlopen(Request(url,headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:57.0) Gecko/20100101 Firefox/57.0'}))
		try:
			soup = BeautifulSoup(page,'html.parser')
			try:
				title = soup.title.string.encode('utf-8').decode() ## clumsy!!
				title = (title[:197] + '...') if len(title) > 197 else title
				return title, '200'
			except:
				error_code = '404'
		except:
			print('Beautiful Soup Error')
			error_code = '500'
			raise  #  Need to find out what errors BS4 will raise
	except HTTPError as e:
		print("HTTPError:", e.reason)
		error_code = e.code
	except URLError as e:
		print("URLError:", e.reason)
		error_code = '400'
	except ValueError:
		print("ValueError: URL format rejected")
		error_code = '400'
	except ContentTooShortError as e:
		error_code = '500'
	except RemoteDisconnected as e:
		pass

	return None, error_code

def get_json_ld_headline(url):

	headline = None
	error_code = None

	## TODO: Get detail on the errors

	try:
		r = requests.get(url, timeout=5)
	except:
		error_code = '404'
		return headline, error_code

	try:
		base_url = get_base_url(r.text, r.url)
	except:
		error_code = '500'
		return headline, error_code

	try:
		data = extruct.extract(r.text, base_url=base_url,syntaxes=['json-ld']) #
	except Exception as e:
		error_code = '500'
		return headline, error_code

	jl = data['json-ld']

	for l in jl:
		if l.get('headline',None):
			headline = l['headline']
			headline = (headline[:197] + '...') if len(headline) > 197 else headline


	return headline, '200'

def get_opengraph_title(url):

	title = None
	error_code = None

	## TODO: Get detail on the errors

	try:
		r = requests.get(url, timeout=5)
	except:
		error_code = '404'
		return title, error_code

	try:
		base_url = get_base_url(r.text, r.url)
	except:
		error_code = '500'
		return title, error_code

	try:
		data = extruct.extract(r.text, base_url=base_url,syntaxes=['opengraph']) #
	except Exception as e:
		error_code = '500'
		return title, error_code

	og = data['opengraph']

	for o in og:
		if o.get('properties',None):
			for i in o['properties']:
				if i[0] == 'og:title':
					title = i[1]
					title = (title[:197] + '...') if len(title) > 197 else title


	return title, '200'

def get_description(url):
	error_code = None
	decription = None

	description, error_code = get_opengraph_description(url)
	print('og:description:', description, error_code)

	if not description:
		description, error_code = get_json_ld_description(url)
		print('jl description:', description, error_code)

	return description, error_code

def get_json_ld_description(url):

	description = None
	error_code = None

	## TODO: Get detail on the errors

	try:
		r = requests.get(url, timeout=5)
	except:
		error_code = '404'
		return description, error_code

	try:
		base_url = get_base_url(r.text, r.url)
	except:
		error_code = '500'
		return description, error_code

	try:
		data = extruct.extract(r.text, base_url=base_url,syntaxes=['json-ld']) #
	except Exception as e:
		error_code = '500'
		return description, error_code

	jl = data['json-ld']

	for l in jl:
		if l.get('description',None):
			description = l['description']

	return description, '200'

def get_opengraph_description(url):

	description = None
	error_code = None

	## TODO: Get detail on the errors

	try:
		r = requests.get(url, timeout=5)
	except:
		error_code = '404'
		return description, error_code

	try:
		base_url = get_base_url(r.text, r.url)
	except:
		error_code = '500'
		return description, error_code

	try:
		data = extruct.extract(r.text, base_url=base_url,syntaxes=['opengraph']) #
	except Exception as e:
		error_code = '500'
		return description, error_code

	og = data['opengraph']

	for o in og:
		if o.get('properties',None):
			for i in o['properties']:
				if i[0] == 'og:description':
					description = i[1]

	return description, '200'

def check_duplicate_link(url,profile):

	''' Return true if a duplicate Link record is found '''

	if get_object_or_None(Link,url=url, profile=profile):
		return True
	return False