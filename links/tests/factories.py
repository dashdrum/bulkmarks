import factory
import random
import datetime
from django.utils import timezone


from links.models import (Link, Profile, InterfaceFile)

from django.contrib.auth.models import User

class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user' + n, str)
    last_name = factory.Sequence(lambda n: 'last' + n, str)
    first_name = factory.Sequence(lambda n: 'first' + n, str)
    email = factory.Sequence(lambda n: 'mailbox' + n + '@bulkmarks.com', str)

class ProfileFactory(factory.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    display_name = factory.Sequence(lambda n: 'displayname' + n, str)

class LinkFactory(factory.DjangoModelFactory):
    class Meta:
        model = Link

    title = factory.Sequence(lambda n:  'title' + n, str)
    url = factory.Sequence(lambda n: 'https://bulkmarks.com/' + n, str)
    comment = factory.Sequence(lambda n:  'comment' + n, str)
    status = random.choice('RENO')
    profile = factory.SubFactory(ProfileFactory)
    tested_on = factory.LazyFunction(timezone.now)

class InterfaceFileFactory(factory.DjangoModelFactory):
    class Meta:
        model = InterfaceFile

    profile = factory.SubFactory(ProfileFactory)
    file_name = factory.Sequence(lambda n:  'title' + n, str)
    file_type  = random.choice('IE')
    file_format  = random.choice('DN')