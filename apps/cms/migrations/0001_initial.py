# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-04-27 06:07
from __future__ import unicode_literals

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CmsPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', tinymce.models.HTMLField()),
                ('slug', models.SlugField(blank=True, max_length=40, null=True, unique=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
