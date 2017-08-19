''' Shared utility functions '''

from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError, ContentTooShortError
from bs4 import BeautifulSoup



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

	return None, error_code

