# Generated by Django 4.2.7 on 2025-05-13 15:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Share',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.PositiveIntegerField()),
                ('permission_type', models.CharField(choices=[('VIEW', 'View Only'), ('COMMENT', 'Comment'), ('EDIT', 'Edit'), ('ADMIN', 'Admin')], default='VIEW', max_length=10)),
                ('is_public', models.BooleanField(default=False)),
                ('password', models.CharField(blank=True, max_length=255, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('access_count', models.PositiveIntegerField(default=0)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shares_created', to=settings.AUTH_USER_MODEL)),
                ('shared_with', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='shares_received', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Share',
                'verbose_name_plural': 'Shares',
            },
        ),
        migrations.CreateModel(
            name='AccessLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('accessed_at', models.DateTimeField(auto_now_add=True)),
                ('password_used', models.BooleanField(default=False)),
                ('share', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_logs', to='shares.share')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-accessed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='share',
            index=models.Index(fields=['content_type', 'object_id'], name='shares_shar_content_7aad5d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='share',
            unique_together={('content_type', 'object_id', 'shared_with')},
        ),
    ]
