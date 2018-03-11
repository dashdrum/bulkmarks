''' Shared utility functions '''

from datetime import datetime

from django.utils.timezone import make_aware, utc
from annoying.functions import get_object_or_None

from .models import Link

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
