# Generated by Django 3.2.16 on 2023-06-07 21:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newBernTOD', '0009_auto_20230607_1720'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalparcel',
            name='reid',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='reid',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
