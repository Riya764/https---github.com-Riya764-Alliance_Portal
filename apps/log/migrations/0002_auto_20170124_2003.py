# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-01-24 14:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='request_content_length',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Request size in Kilobyte.'),
        ),
        migrations.AlterField(
            model_name='log',
            name='response_content_length',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Response size in Kilobyte.'),
        ),
    ]
