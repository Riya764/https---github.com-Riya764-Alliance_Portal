# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-06-21 09:49
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0002_auto_20170615_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='net_rate',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0.9), django.core.validators.MaxValueValidator(10000.99)], verbose_name='Invoice Price (\u20b9)'),
        ),
    ]