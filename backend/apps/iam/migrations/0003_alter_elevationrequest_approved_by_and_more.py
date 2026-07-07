from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('iam', '0002_elevationrequest'),
    ]

    operations = [
        migrations.RemoveField(model_name='elevationrequest', name='approved_by'),
        migrations.AddField(
            model_name='elevationrequest', name='approved_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_elevations',
                to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(model_name='elevationrequest', name='user'),
        migrations.AddField(
            model_name='elevationrequest', name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='elevation_requests',
                to=settings.AUTH_USER_MODEL),
        ),
    ]
