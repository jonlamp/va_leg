# Generated by Django 4.1.5 on 2023-01-19 03:51

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_remove_bill_session_bill_patrons_alter_patron_bill_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="action",
            name="d_added",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]