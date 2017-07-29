# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-03 18:13
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Link',
            fields=[
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='created on')),
                ('updated_on', models.DateTimeField(editable=False, verbose_name='updated on')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('url', models.URLField(max_length=400)),
                ('comment', models.TextField(blank=True, max_length=1000, null=True)),
                ('public', models.BooleanField(default=True)),
                ('status', models.CharField(blank=True, max_length=1, null=True)),
                ('tested_on', models.DateTimeField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]