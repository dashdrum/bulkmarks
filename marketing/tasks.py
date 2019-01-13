
from django.core.mail import send_mail

from django.template.loader import render_to_string

from bulk.celery import app


#-----------------------------------------------------------------------------#



@app.task()
def send_signup_email(email):

	sender = 'infobot@bulkmarks.com'
	subject = 'Bulkmarks Signup Received'

	message = render_to_string('signup_received_email.html', {
		'email': email,
	})

	send_mail(subject, message, sender,['info@bulkmarks.com'],fail_silently=True)


