# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2020-01-24 11:47
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0015_auto_20200106_1842'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributorstock',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2020, 1, 24, 11, 47, 19, 132575, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='distributorstock',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2020, 1, 24, 11, 47, 19, 132607, tzinfo=utc)),
        ),
    ]