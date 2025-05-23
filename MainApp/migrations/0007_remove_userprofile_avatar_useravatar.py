# Generated by Django 4.2.1 on 2025-04-17 11:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('MainApp', '0006_event_is_free'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='avatar',
        ),
        migrations.CreateModel(
            name='UserAvatar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='avatars/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('is_current', models.BooleanField(default=False)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='avatars', to='MainApp.userprofile')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
