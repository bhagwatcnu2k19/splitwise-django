# Generated by Django 2.2.4 on 2019-08-09 16:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('split', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='balance',
            old_name='expense_id',
            new_name='expense',
        ),
        migrations.RenameField(
            model_name='expense',
            old_name='category_id',
            new_name='category',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='expense_id',
            new_name='expense',
        ),
        migrations.RenameField(
            model_name='transaction',
            old_name='user_id',
            new_name='user',
        ),
    ]
