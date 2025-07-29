from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shares', '0002_shareemailnotification'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='eventinvitation',
            name='share',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='event_invitation',
                to='shares.share',
                help_text='References the share that created this invitation (optional for public RSVPs)'
            ),
        ),
    ]