# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-06-15 11:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0002_auto_20170525_0931'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='from_email',
            field=models.CharField(default=b'HUL Team <no-reply@hul.com>', max_length=255),
        ),
    ]