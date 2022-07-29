# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2022-07-16 18:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0020_auto_20220612_1557'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='alliancepartnerorderdetail',
        #     name='invoice_number_alliance',
        #     field=models.CharField(blank=True, max_length=100, null=True),
        # ),
        migrations.AddField(
            model_name='distributororderdetail',
            name='returned_units',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='cgst_total',
            field=models.FloatField(default=0, verbose_name='CGST Total (?)'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='dis_total',
            field=models.FloatField(default=0, verbose_name='Discount Total (?)'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='invoice_number_alliance',
            field=models.CharField(blank=True, help_text='This is received from Alliance csv', max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='sgst_total',
            field=models.FloatField(default=0, verbose_name='SGST Total (?)'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorder',
            name='sta_total',
            field=models.FloatField(default=0, verbose_name='Stales Disc Total (?)'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorderdetail',
            name='base_price_par_unit',
            field=models.FloatField(default=0, verbose_name='Base Price Per Unit (?)'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorderdetail',
            name='cash_discount',
            field=models.FloatField(default=0, help_text='Cash Discount'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorderdetail',
            name='discount_amount',
            field=models.FloatField(default=0, verbose_name='Discount (\u20b9)'),
        ),
        migrations.AlterField(
            model_name='alliancepartnerorderdetail',
            name='total_amt_base_peice',
            field=models.FloatField(default=0, verbose_name='Total Amt (Base price) (?)'),
        ),
        migrations.AlterField(
            model_name='distributororder',
            name='cgst_total',
            field=models.FloatField(default=0, null=True, verbose_name='CGST Total (?)'),
        ),
        migrations.AlterField(
            model_name='distributororder',
            name='igst_total',
            field=models.FloatField(default=0, null=True, verbose_name='IGST Total (?)'),
        ),
        migrations.AlterField(
            model_name='distributororder',
            name='sgst_total',
            field=models.FloatField(default=0, null=True, verbose_name='SGST Total (?)'),
        ),
        migrations.AlterField(
            model_name='distributorstock',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='distributorstock',
            name='modified',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
