# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-03-11 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='reg_email_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
