# Generated by Django 3.2.6 on 2021-08-09 16:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_profile_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(default='default-avatar.png', upload_to='profile_images'),
        ),
    ]
