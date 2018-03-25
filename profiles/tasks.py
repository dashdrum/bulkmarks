from html.parser import HTMLParser
from html.entities import name2codepoint
from datetime import datetime, timezone
import time

from django.utils.timezone import make_aware, utc
from django.db import IntegrityError, DataError
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text

from annoying.functions import get_object_or_None
from bs4 import BeautifulSoup

from bulk.celery import app


from .models import Profile
from .tokens import account_activation_token


#-----------------------------------------------------------------------------#



@app.task()
def send_activation_email(user,request):

	sender = 'infobot@bulkmarks.com'
	subject = 'Activate Your Bulkmarks Account'
	current_site = get_current_site(request)

	message = render_to_string('account_activation_email.html', {
		'user': user,
		'domain': current_site.domain,
		'uid': urlsafe_base64_encode(force_bytes(user.pk)),
		'token': account_activation_token.make_token(user),
	})

	print('Sending Activation Email')
	user.email_user(subject, message, from_email=sender)


