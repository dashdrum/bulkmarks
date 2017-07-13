from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import datetime

class Link(object):
	title = ''
	href = ''
	private = False
	add_date = None
	tags = ''
	notes = ''

	def __str__(self):
		return ('Link:' + self.title + ', ' + self.href + ', ' + str(self.private) + ', '
						+ str(self.add_date) + ', ' + self.tags + ', ' + self.notes)

class MyHTMLParser(HTMLParser):

	current_tag = None
	current_link = None

	def handle_starttag(self, tag, attrs):

		self.current_tag = tag

		if tag == 'dt':
			if self.current_link:
				# if self.current_link.private is True:
					print(self.current_link)
				# self.current_link.save()
			self.current_link = Link()
			# print('Entry')
		elif tag == 'a':
			attr_dict = dict(attrs)
			self.current_link.href = attr_dict.get('href',None)
			self.current_link.private = bool(int(attr_dict['private']))
			self.current_link.add_date = datetime.utcfromtimestamp(float(attr_dict['add_date']))
			self.current_link.tags = attr_dict['tags']
		elif tag == 'dd':
			None

	def handle_data(self, data):
		if data != '\n':
			if self.current_tag == 'a':
				self.current_link.title = data
			elif self.current_tag == 'dd':
				self.current_link.notes = data

parser = MyHTMLParser()

file = open('delicious.html', 'r')

parser.feed(file.read())





