# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2018-07-11 04:10
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app', '0010_auto_20180711_0940'),
        ('product', '0004_auto_20180711_0940'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiscountToShakti',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('discount_type', models.PositiveSmallIntegerField(choices=[(1, 'Percentage'), (2, 'Cash')], default=1)),
                ('discount', models.PositiveIntegerField()),
                ('regional_distributor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='distributoroffers', to='app.RegionalDistributor', to_field='user_id')),
            ],
            options={
                'db_table': 'offers_shaktidiscount',
                'verbose_name': 'Discount to Shakti',
                'verbose_name_plural': 'Discount to Shakti',
            },
        ),
        migrations.CreateModel(
            name='PromotionLines',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('buy_quantity', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Buy Quantity (in Units)')),
                ('free_quantity', models.PositiveIntegerField(blank=True, null=True)),
                ('discount', models.PositiveIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(99), django.core.validators.MinValueValidator(1)], verbose_name='Discount (%)')),
                ('buy_product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offers_promotionlines_related', to='product.Product')),
                ('free_product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='free_product', to='product.Product')),
            ],
        ),
        migrations.CreateModel(
            name='Promotions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=100, unique=True)),
                ('discount_type', models.PositiveSmallIntegerField(choices=[(0, 'Percentange'), (1, 'Quantity'), (2, 'Quantity off for all')])),
                ('start', models.DateField()),
                ('end', models.DateField(verbose_name='Expires on')),
                ('shakti_enterpreneur', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='offers_promotions_related', to='app.ShaktiEntrepreneur', to_field='user')),
            ],
        ),
        migrations.CreateModel(
            name='ShaktiBonus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('start', models.DateField()),
                ('end', models.DateField(verbose_name='Expires on')),
                ('shakti_enterpreneur', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.ShaktiEntrepreneur', to_field='user')),
            ],
            options={
                'verbose_name_plural': 'Shakti Bonus',
            },
        ),
        migrations.CreateModel(
            name='ShaktiBonusLines',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('target_amount', models.PositiveIntegerField()),
                ('discount_type', models.SmallIntegerField(choices=[(1, 'Percentage'), (2, 'Cash')], default=1)),
                ('discount', models.PositiveIntegerField(verbose_name='Discount')),
                ('shakti_bonus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offers.ShaktiBonus')),
            ],
            options={
                'verbose_name': 'Shakti Bonus Lines',
                'verbose_name_plural': 'Shakti Bonus Lines',
            },
        ),
        migrations.AddField(
            model_name='promotionlines',
            name='promotion',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='offers.Promotions'),
        ),
        migrations.CreateModel(
            name='ShaktiBonusAll',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Bonus to All',
            },
            bases=('offers.shaktibonus',),
        ),
        migrations.CreateModel(
            name='ShaktiBonusAllLines',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Bonus to All Lines',
            },
            bases=('offers.shaktibonuslines',),
        ),
        migrations.CreateModel(
            name='ShaktiOffers',
            fields=[
            ],
            options={
                'verbose_name': 'Shakti Offers',
                'proxy': True,
                'verbose_name_plural': 'Shakti Offers',
            },
            bases=('offers.promotions',),
        ),
        migrations.CreateModel(
            name='ShaktiOffersLines',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Shakti offer Lines',
            },
            bases=('offers.promotionlines',),
        ),
        migrations.CreateModel(
            name='ShaktiPromotionLines',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Shakti Promotion Lines',
            },
            bases=('offers.promotionlines',),
        ),
        migrations.CreateModel(
            name='ShaktiPromotions',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Shakti Promotions',
            },
            bases=('offers.promotions',),
        ),
        migrations.CreateModel(
            name='TradeOffers',
            fields=[
            ],
            options={
                'verbose_name': 'Trade Offers',
                'proxy': True,
                'verbose_name_plural': 'Trade Offers',
            },
            bases=('offers.promotions',),
        ),
        migrations.CreateModel(
            name='TradeOffersLines',
            fields=[
            ],
            options={
                'proxy': True,
                'verbose_name_plural': 'Trade offers Lines',
            },
            bases=('offers.promotionlines',),
        ),
        migrations.AlterUniqueTogether(
            name='shaktibonuslines',
            unique_together=set([('shakti_bonus', 'target_amount')]),
        ),
    ]
