# Generated by Django 3.1.3 on 2020-12-23 12:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gifterator', '0007_auto_20201223_1148'),
    ]

    operations = [
        migrations.RenameField(
            model_name='giftlistitem',
            old_name='nickname',
            new_name='name',
        ),
    ]