# Generated by Django 3.1.3 on 2020-12-21 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gifterator', '0002_exchangeparticipant_email_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangeparticipant',
            name='email_last_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
