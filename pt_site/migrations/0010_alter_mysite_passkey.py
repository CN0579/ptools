# Generated by Django 4.1 on 2022-09-16 10:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pt_site", "0009_alter_downloader_category_alter_site_mailbox_rule_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mysite",
            name="passkey",
            field=models.CharField(
                blank=True, max_length=128, null=True, verbose_name="PassKey"
            ),
        ),
    ]
