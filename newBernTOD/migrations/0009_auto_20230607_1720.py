# Generated by Django 3.2.16 on 2023-06-07 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newBernTOD', '0008_overlay'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalparcel',
            name='addr1',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='addr2',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='addr3',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='bldg_val',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='deed_acres',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=11, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='land_val',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='propdesc',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='total_value_assd',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='totsalprice',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=11, null=True),
        ),
        migrations.AddField(
            model_name='historicalparcel',
            name='year_built',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='addr1',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='addr2',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='addr3',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='bldg_val',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='deed_acres',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=11, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='land_val',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='propdesc',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='total_value_assd',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='totsalprice',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=11, null=True),
        ),
        migrations.AddField(
            model_name='parcel',
            name='year_built',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
