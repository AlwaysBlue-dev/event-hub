# Generated by Django 4.2.1 on 2025-04-19 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MainApp', '0008_event_map_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='city',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='event',
            name='country',
            field=models.CharField(default='Pakistan', max_length=100),
        ),
    ]
