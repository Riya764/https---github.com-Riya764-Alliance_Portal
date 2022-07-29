# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-07-11 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_auto_20170621_0949'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributororder',
            name='order_status',
            field=models.IntegerField(choices=[(1, b'ORDERED'), (2, b'CONFIRMED'), (3, b'SHIPPED'), (4, b'READY FOR PICKUP'), (5, b'DISPATCHED'), (6, b'DELIVERED'), (7, b'CANCELLED'), (9, b'RETURNED')], default=1),
        ),
        migrations.AlterField(
            model_name='distributororderdetail',
            name='item_status',
            field=models.IntegerField(choices=[(1, b'ORDERED'), (2, b'CONFIRMED'), (3, b'SHIPPED'), (4, b'READY FOR PICKUP'), (5, b'DISPATCHED'), (6, b'DELIVERED'), (7, b'CANCELLED'), (9, b'RETURNED')], default=1),
        ),
    ]