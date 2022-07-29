# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-05-19 07:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_auto_20170508_0654'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributororder',
            name='order_status',
            field=models.IntegerField(choices=[(1, b'ORDERED'), (2, b'CONFIRMED'), (3, b'SHIPPED'), (4, b'READY FOR PICKUP'), (5, b'DISPATCHED'), (6, b'DELIVERED'), (8, b'DISCARDED'), (7, b'CANCELLED')], default=1),
        ),
        migrations.AlterField(
            model_name='distributororderdetail',
            name='item_status',
            field=models.IntegerField(choices=[(1, b'ORDERED'), (2, b'CONFIRMED'), (3, b'SHIPPED'), (4, b'READY FOR PICKUP'), (5, b'DISPATCHED'), (6, b'DELIVERED'), (8, b'DISCARDED'), (7, b'CANCELLED')], default=1),
        ),
    ]