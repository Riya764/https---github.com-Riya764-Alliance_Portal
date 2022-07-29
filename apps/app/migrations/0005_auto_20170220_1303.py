# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-20 07:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20170220_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forgotpassword',
            name='otp_status_type',
            field=models.CharField(choices=[(2, 'SUCCESS'), (4, 'USED'), (0, 'PENDING'), (1, 'VERIFIED'), (3, 'ERROR')], default=0, max_length=250),
        ),
    ]
