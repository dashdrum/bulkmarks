from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError, ContentTooShortError
from http.client import RemoteDisconnected

from bs4 import BeautifulSoup
from annoying.functions import get_object_or_None



def get_title(url):
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