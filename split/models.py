from django.db import models
from django.contrib.auth.models import User


# Create your models here.

# ADD FOREIGN KEYS AND CASCADING


class Category(models.Model):
    name = models.CharField(max_length=200)


class Expense(models.Model):
    description = models.CharField(max_length=200, null=False, blank=False)
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, null=False, blank=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=False)
    # category_id = models.IntegerField()
    deleted = models.BooleanField(null=False, default=False)
    month_number = models.IntegerField()


class Balance(models.Model):
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=False, blank=False)
    ower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrower', blank=False)
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lender', blank=False)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, blank=False)


class Transaction(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    owe = models.DecimalField(max_digits=20, decimal_places=2, null=False, blank=False)
    lend = models.DecimalField(max_digits=20, decimal_places=2, null=False, blank=False)
    # expense_id = models.IntegerField()
