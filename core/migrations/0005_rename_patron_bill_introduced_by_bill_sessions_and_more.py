# Generated by Django 4.1.5 on 2023-01-16 23:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_rename_d_introducted_bill_d_introduced"),
    ]

    operations = [
        migrations.RenameField(
            model_name="bill",
            old_name="patron",
            new_name="introduced_by",
        ),
        migrations.AddField(
            model_name="bill",
            name="sessions",
            field=models.ManyToManyField(to="core.session"),
        ),
        migrations.CreateModel(
            name="Patron",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("patron_type", models.CharField(max_length=40)),
                (
                    "bill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patrons",
                        to="core.bill",
                    ),
                ),
                (
                    "legislator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patrons",
                        to="core.legislator",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Action",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("d_action", models.DateTimeField()),
                ("description", models.CharField(max_length=300)),
                ("refid", models.CharField(max_length=40, null=True)),
                (
                    "bill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="actions",
                        to="core.bill",
                    ),
                ),
            ],
        ),
    ]