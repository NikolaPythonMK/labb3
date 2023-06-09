# Generated by Django 4.0.4 on 2022-05-24 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blogsite', '0003_alter_appuser_username'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appuser',
            name='blocked_by',
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='date_created',
            field=models.DateField(verbose_name='Date Of Creation'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='last_modified',
            field=models.DateTimeField(verbose_name='Date Of Last Modification'),
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateField()),
                ('content', models.TextField()),
                ('app_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blogsite.appuser')),
                ('blog_post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='blogsite.blogpost')),
            ],
        ),
    ]
