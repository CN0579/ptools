# Generated by Django 4.1.2 on 2022-12-25 21:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pt_site', '0021_alter_mysite_cookie_alter_mysite_user_agent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mysite',
            name='user_id',
            field=models.CharField(help_text='请填写<font color="orangered">数字UID</font>，<font color="orange">* 莫妮卡请填写用户名</font>', max_length=16, verbose_name='用户ID'),
        ),
    ]
