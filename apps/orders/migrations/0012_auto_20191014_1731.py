# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2019-10-14 12:01
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_auto_20190716_1135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributorstock',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2019, 10, 14, 12, 1, 50, 802582, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='distributorstock',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2019, 10, 14, 12, 1, 50, 802614, tzinfo=utc)),
        ),
    ]
