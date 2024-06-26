# Generated by Django 5.0.1 on 2024-02-10 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0013_rename_f_name_userprofile_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='resolved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='chat',
            name='status',
            field=models.CharField(blank=True, choices=[('new', 'New'), ('resolved', 'Resolved'), ('pending', 'Pending')], max_length=10, null=True),
        ),
    ]
