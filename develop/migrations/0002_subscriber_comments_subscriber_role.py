# Generated by Django 4.1.8 on 2023-07-02 21:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("develop", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriber",
            name="comments",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="subscriber",
            name="role",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]