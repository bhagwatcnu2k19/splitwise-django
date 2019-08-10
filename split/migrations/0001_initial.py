# Generated by Django 2.2.4 on 2019-08-09 15:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('deleted', models.BooleanField(default=False)),
                ('category_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='split.Category')),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('owe', models.DecimalField(decimal_places=2, max_digits=20)),
                ('lend', models.DecimalField(decimal_places=2, max_digits=20)),
                ('expense_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='split.Expense')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Balance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=20)),
                ('expense_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='split.Expense')),
                ('lender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lender', to=settings.AUTH_USER_MODEL)),
                ('ower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrower', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
