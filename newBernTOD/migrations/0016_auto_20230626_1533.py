# Generated by Django 3.2.16 on 2023-06-26 19:33

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newBernTOD', '0015_overlay2'),
    ]

    operations = [
        migrations.CreateModel(
            name='NCOD',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('objectid', models.IntegerField()),
                ('overlay', models.CharField(max_length=4)),
                ('olay_decod', models.CharField(max_length=42)),
                ('olay_name', models.CharField(max_length=25)),
                ('zone_case', models.CharField(max_length=9)),
                ('ordinance', models.CharField(max_length=8)),
                ('eff_date', models.DateField()),
                ('overlay_ty', models.CharField(max_length=28)),
                ('shape_leng', models.FloatField()),
                ('shape_area', models.FloatField()),
                ('geom', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('modified_date', models.DateTimeField(auto_now=True)),
                ('parcels', models.ManyToManyField(blank=True, default=None, to='newBernTOD.Parcel')),
            ],
        ),
        migrations.DeleteModel(
            name='Overlay2',
        ),
    ]