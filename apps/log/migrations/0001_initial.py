# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('remote_address', models.CharField(max_length=255, null=True, blank=True)),
                ('user_email', models.CharField(max_length=255, null=True, blank=True)),
                ('method_type', models.CharField(max_length=255, null=True, blank=True)),
                ('method_name', models.CharField(max_length=255, null=True, blank=True)),
                ('access_token', models.CharField(max_length=350, null=True, blank=True)),
                ('request_content_length', models.CharField(max_length=255, null=True, verbose_name=b'Request size in Kilobyte.', blank=True)),
                ('request_content', models.TextField(null=True, blank=True)),
                ('request_datetime', models.DateTimeField(null=True, blank=True)),
                ('response_status_type', models.CharField(max_length=255, null=True, blank=True)),
                ('response_content', models.TextField(null=True, blank=True)),
                ('response_content_length', models.CharField(max_length=255, null=True, verbose_name=b'Response size in Kilobyte.', blank=True)),
                ('response_datetime', models.DateTimeField(null=True, blank=True)),
                ('total_time_taken', models.FloatField(null=True, blank=True)),
                ('extra_log', models.TextField(null=True, blank=True)),
                ('exception_full_stack_trace', models.TextField(null=True, blank=True)),
                ('exception_short_value', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
    ]
