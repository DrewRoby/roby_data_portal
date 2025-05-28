from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shares', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=300)),
                ('is_public', models.BooleanField(default=False, help_text='Allow anyone to view this event (login required for RSVP/comments)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', '-start_time'],
            },
        ),
        migrations.CreateModel(
            name='Space',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('space_type', models.CharField(choices=[('normal', 'Normal Space'), ('suggestion_box', 'Suggestion Box')], default='normal', max_length=20)),
                ('order', models.PositiveIntegerField(default=0)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spaces', to='events.event')),
            ],
            options={
                'ordering': ['order', 'name'],
                'unique_together': {('event', 'name')},
            },
        ),
        migrations.CreateModel(
            name='AgendaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('duration_minutes', models.PositiveIntegerField(default=30, help_text='Duration in minutes')),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agenda_items', to='events.space')),
                ('suggested_by', models.ForeignKey(blank=True, help_text='User who suggested this item (if applicable)', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='EventInvitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rsvp_status', models.CharField(choices=[('pending', 'Pending'), ('yes', 'Yes'), ('no', 'No'), ('tentative', 'Tentative')], default='pending', max_length=10)),
                ('rsvp_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='events.event')),
                ('invitee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_invitations', to=settings.AUTH_USER_MODEL)),
                ('share', models.OneToOneField(help_text='References the share that created this invitation', on_delete=django.db.models.deletion.CASCADE, related_name='event_invitation', to='shares.share')),
            ],
            options={
                'unique_together': {('event', 'invitee')},
            },
        ),
        migrations.CreateModel(
            name='AgendaComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('agenda_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='events.agendaitem')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]