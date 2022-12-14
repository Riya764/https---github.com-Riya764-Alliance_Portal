# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-07-07 07:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0003_auto_20170615_1110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='email',
            name='sent_status_type',
            field=models.IntegerField(choices=[(1, b'PENDING'), (2, b'INPROGRESS'), (3, b'SUCCESS'), (4, b'ERROR'), (5, b'NOTIFICATIONS OFF')], default=1),
        ),
        migrations.AlterField(
            model_name='mobilenotification',
            name='sent_status_type',
            field=models.IntegerField(choices=[(1, b'PENDING'), (2, b'INPROGRESS'), (3, b'SUCCESS'), (4, b'ERROR'), (5, b'NOTIFICATIONS OFF')], default=1),
        ),
    ]
