# Generated by Django 4.2.1 on 2025-04-16 09:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('MainApp', '0003_event_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='highlights',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='EventFace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='event_faces/')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='faces', to='MainApp.event')),
            ],
        ),
    ]
