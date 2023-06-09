# Generated by Django 3.2.16 on 2023-06-27 00:07

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newBernTOD', '0017_auto_20230626_1910'),
    ]

    operations = [
        migrations.CreateModel(
            name='HOD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('objectid', models.IntegerField()),
                ('overlay', models.CharField(max_length=5)),
                ('olay_decod', models.CharField(max_length=36)),
                ('olay_name', models.CharField(max_length=17)),
                ('zone_case', models.CharField(max_length=10)),
                ('ordinance', models.CharField(max_length=8)),
                ('eff_date', models.DateField()),
                ('overlay_ty', models.CharField(max_length=28)),
                ('shape_leng', models.FloatField()),
                ('shape_area', models.FloatField()),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
            ],
        ),
    ]
