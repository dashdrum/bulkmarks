# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-29 15:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Signup',
            fields=[
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created on')),
                ('updated_on', models.DateTimeField(editable=False, verbose_name='updated on')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('reg_allowed', models.BooleanField(default=False)),
                ('invite_sent', models.DateField()),
                ('status', models.CharField(default='N', max_length=1)),
            ],
            options={
                'permissions': (('view_signup', 'Can view signups'),),
            },
        ),
    ]
