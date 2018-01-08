# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-12-06 11:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apr', '0006_auto_20171106_0834'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ShipInfo',
        ),
        migrations.RemoveField(
            model_name='requestelement',
            name='schedule',
        ),
        migrations.AddField(
            model_name='requiredinformation',
            name='schedule',
            field=models.IntegerField(default=0),
        ),
    ]
