# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-05 00:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('taggit', '0002_auto_20150616_2121'),
        ('links', '0008_auto_20171005_0037'),
    ]

    operations = [
        migrations.CreateModel(
            name='GenericUUIDTaggedItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.UUIDField(db_index=True, verbose_name='Object id')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links_genericuuidtaggeditem_tagged_items', to='contenttypes.ContentType', verbose_name='Content type')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links_genericuuidtaggeditem_items', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='link',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='links.GenericUUIDTaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]