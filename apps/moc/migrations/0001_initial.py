# -*- coding: utf-8 -*-
# Generated by Django 1.9.11 on 2019-07-16 06:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MoCMonth',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=50)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
            options={
                'ordering': ('-start_date', 'moc_year'),
                'verbose_name': 'MoC Month',
                'verbose_name_plural': 'MoC Months',
            },
        ),
        migrations.CreateModel(
            name='MoCYear',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('year', models.PositiveIntegerField(unique=True, verbose_name='MoC Year')),
            ],
            options={
                'verbose_name': 'MoC Year',
                'verbose_name_plural': 'MoC Years',
            },
        ),
        migrations.AddField(
            model_name='mocmonth',
            name='moc_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moc_year', to='moc.MoCYear'),
        ),
    ]