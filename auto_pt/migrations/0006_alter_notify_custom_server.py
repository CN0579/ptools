# Generated by Django 4.1.2 on 2022-12-25 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auto_pt', '0005_alter_taskjob_replace_existing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notify',
            name='custom_server',
            field=models.URLField(blank=True, help_text='IYuu与BARK请必填，详情参考教程！', null=True, verbose_name='服务器'),
        ),
    ]
