from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('portal', '0001_create_user_profile_and_verification'),
    ]

    operations = [
        migrations.CreateModel(
            name='App',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_id', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('icon', models.CharField(help_text='Icon class or name', max_length=50)),
                ('background_color', models.CharField(default='#ffffff', max_length=20)),
                ('link', models.CharField(max_length=100)),
                ('is_default', models.BooleanField(default=False)),
                ('order', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='UserAppAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('granted_date', models.DateTimeField(auto_now_add=True)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='portal.app')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='app_access_new', to='auth.user')),
            ],
            options={
                'verbose_name_plural': 'User App Access',
                'unique_together': {('user', 'app')},
            },
        ),
    ]