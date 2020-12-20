# Generated by Django 3.1.3 on 2020-12-20 22:12

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('session_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appuser',
            name='privacy_policy_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='appuser',
            name='user_consent_timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]