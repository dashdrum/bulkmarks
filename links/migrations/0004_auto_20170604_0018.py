# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-04 00:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0003_link_profile'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='link',
            name='user',
        ),
        migrations.AlterField(
            model_name='link',
            name='profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='links.Profile'),
        ),
    ]
