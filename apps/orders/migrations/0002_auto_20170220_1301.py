# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-20 07:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='order_status',
            field=models.CharField(choices=[('delievered', 'DELIEVERED'), ('cancelled', 'CANCELLED'), ('dispatched', 'DISPATCHED'), ('pending', 'PENDING'), ('confirmed', 'CONFIRMED')], default='pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='payment_status',
            field=models.CharField(choices=[('paid', 'PAID'), ('pending', 'PENDING'), ('received', 'RECEIVED')], default='pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorderdetail',
            name='item_status',
            field=models.CharField(choices=[('delievered', 'DELIEVERED'), ('cancelled', 'CANCELLED'), ('dispatched', 'DISPATCHED'), ('pending', 'PENDING'), ('confirmed', 'CONFIRMED')], default='pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='distributororder',
            name='order_status',
            field=models.CharField(choices=[('delievered', 'DELIEVERED'), ('cancelled', 'CANCELLED'), ('dispatched', 'DISPATCHED'), ('pending', 'PENDING'), ('confirmed', 'CONFIRMED')], default='confirmed', max_length=10),
        ),
        migrations.AlterField(
            model_name='distributororder',
            name='payment_status',
            field=models.CharField(choices=[('paid', 'PAID'), ('pending', 'PENDING'), ('received', 'RECEIVED')], default='pending', max_length=10),
        ),
        migrations.AlterField(
            model_name='distributororderdetail',
            name='item_status',
            field=models.CharField(choices=[('delievered', 'DELIEVERED'), ('cancelled', 'CANCELLED'), ('dispatched', 'DISPATCHED'), ('pending', 'PENDING'), ('confirmed', 'CONFIRMED')], default='pending', max_length=10),
        ),
    ]