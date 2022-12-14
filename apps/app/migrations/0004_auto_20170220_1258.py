# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-20 07:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20170220_1257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forgotpassword',
            name='otp_status_type',
            field=models.CharField(choices=[(4, 'USED'), (1, 'VERIFIED'), (3, 'ERROR'), (0, 'PENDING'), (2, 'SUCCESS')], default=0, max_length=250),
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='address_type',
            field=models.CharField(choices=[('recepient', 'RECEPIENT'), ('sender', 'SENDER')], default='sender', max_length=100),
        ),
    ]
