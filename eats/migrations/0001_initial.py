# Generated by Django 4.1.8 on 2023-07-10 23:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Business",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date_added",
                    models.DateTimeField(auto_now_add=True, verbose_name="Date added."),
                ),
                ("name", models.CharField(max_length=200)),
                ("link", models.URLField(max_length=500)),
                ("description", models.TextField(blank=True, default=None, null=True)),
                (
                    "latitude",
                    models.IntegerField(
                        blank=True, default=None, null=True, verbose_name="Latitude"
                    ),
                ),
                (
                    "longitude",
                    models.IntegerField(
                        blank=True, default=None, null=True, verbose_name="Longitude"
                    ),
                ),
                (
                    "has_outdoor_seating",
                    models.BooleanField(verbose_name="Outdoor Seating?"),
                ),
                (
                    "is_temp_closed",
                    models.BooleanField(verbose_name="Temporarily closed?"),
                ),
                ("is_eats", models.BooleanField(verbose_name="Eats")),
                ("is_drinks", models.BooleanField(verbose_name="Drinks")),
                ("is_coffee", models.BooleanField(verbose_name="Coffees")),
                (
                    "is_food_hall",
                    models.BooleanField(default=False, verbose_name="Food Hall?"),
                ),
                ("not_local", models.BooleanField(verbose_name="Not local?")),
                ("open_date", models.DateField()),
                (
                    "close_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="First closed date"
                    ),
                ),
            ],
            options={"verbose_name": "Business", "verbose_name_plural": "Businesses",},
        ),
        migrations.CreateModel(
            name="District",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200, unique=True)),
                ("description", models.TextField(blank=True)),
                ("link", models.URLField(blank=True)),
                ("photo", models.URLField(blank=True)),
                ("district_map", models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="ReferenceLink",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url_link", models.URLField(max_length=500, unique=True)),
                (
                    "description",
                    models.CharField(
                        blank=True, default=None, max_length=500, null=True
                    ),
                ),
                ("headline", models.CharField(max_length=500)),
                (
                    "date_published",
                    models.DateField(blank=True, default=None, null=True),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Reference Link",
                "verbose_name_plural": "Reference Links",
                "ordering": ["-date_created"],
            },
        ),
        migrations.CreateModel(
            name="Vendor",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date_added",
                    models.DateTimeField(auto_now_add=True, verbose_name="Date added."),
                ),
                ("name", models.CharField(max_length=200)),
                ("link", models.URLField(max_length=500)),
                ("description", models.TextField(blank=True, default=None, null=True)),
                (
                    "is_temp_closed",
                    models.BooleanField(verbose_name="Temporarily closed?"),
                ),
                ("not_local", models.BooleanField(verbose_name="Not local?")),
                ("open_date", models.DateField()),
                (
                    "close_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="First closed date"
                    ),
                ),
                (
                    "food_hall",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="eats.business",
                    ),
                ),
            ],
            options={"verbose_name": "Vendor", "verbose_name_plural": "Vendors",},
        ),
        migrations.CreateModel(
            name="Tip",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date",
                    models.DateField(auto_now_add=True, verbose_name="Date added."),
                ),
                ("name", models.CharField(max_length=200)),
                (
                    "link",
                    models.URLField(
                        blank=True, default=None, max_length=500, null=True
                    ),
                ),
                ("description", models.TextField(blank=True, default=None, null=True)),
                (
                    "has_outdoor_seating",
                    models.BooleanField(verbose_name="Outdoor Seating?"),
                ),
                (
                    "is_temp_closed",
                    models.BooleanField(verbose_name="Temporarily closed?"),
                ),
                ("is_eats", models.BooleanField(verbose_name="Eats")),
                ("is_drinks", models.BooleanField(verbose_name="Drinks")),
                ("is_coffee", models.BooleanField(verbose_name="Coffees")),
                (
                    "is_food_hall",
                    models.BooleanField(default=False, verbose_name="Food Hall?"),
                ),
                ("not_local", models.BooleanField(verbose_name="Not local?")),
                ("open_date", models.DateField(blank=True, null=True)),
                ("added", models.BooleanField(verbose_name="Added to Eats?")),
                (
                    "district",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="eats.district",
                    ),
                ),
                (
                    "food_hall",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="eats.business",
                    ),
                ),
                (
                    "references",
                    models.ManyToManyField(
                        blank=True, default=None, to="eats.referencelink"
                    ),
                ),
            ],
            options={"ordering": ["name"],},
        ),
        migrations.CreateModel(
            name="Snapshot",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date", models.DateField(auto_now_add=True)),
                ("local_business_count", models.IntegerField()),
                ("not_local_business_count", models.IntegerField()),
                ("businesses", models.ManyToManyField(to="eats.business")),
            ],
        ),
        migrations.AddField(
            model_name="business",
            name="district",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="eats.district",
            ),
        ),
    ]