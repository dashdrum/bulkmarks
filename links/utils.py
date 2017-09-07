''' Shared utility functions '''

from datetime import datetime

from django.utils.timezone import make_aware, utc

from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError, ContentTooShortError
from http.client import RemoteDisconnected

from bs4 import BeautifulSoup
from annoying.functions import get_object_or_None

from .models import Link, Profile



def get_title(url):
	error_code = None
	title = None

	try:
		## Need to change the agent to fool sites that want to block python bots
		## (Should be harder than this to fool someone)
		page = urlopen(Request(url,headers={'User-Agent': 'Mozilla'}))
		try:
			soup = BeautifulSoup(page,'html.parser')
			try:
				title = soup.title.string.encode('utf-8').decode() ## clumsy!!
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
	except ContentTooShortError as e:
		error_code = 500
	except RemoteDisconnected as e:
		pass

	return None, error_code

def check_duplicate_link(url,profile):

	''' Return true if a duplicate Link record is found '''

	if get_object_or_None(Link,url=url, profile=profile):
		return True
	return False



def get_profile(user):
	try:
		profile = Profile.objects.get(user = user)
		return profile
	except:
		profile = Profile(user=user,display_name=user.username,email=user.email)
		profile.save()
		return profile

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
