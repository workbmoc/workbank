from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='slug',
            field=models.SlugField(max_length=200, unique=False, blank=True, null=True),
        ),
    ]
