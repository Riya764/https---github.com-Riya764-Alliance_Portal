# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-06-21 09:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0006_auto_20170519_0751'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alliancepartnerorderdetail',
            name='unitprice',
            field=models.FloatField(help_text='Net rate from Products table', verbose_name='Invoice Price (\u20b9)'),
        ),
        migrations.AlterField(
            model_name='distributororderdetail',
            name='unitprice',
            field=models.FloatField(verbose_name='TUR (\u20b9)'),
        ),
    ]