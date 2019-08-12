from rest_framework import serializers
from split.models import Expense
from split.models import Balance
from split.models import Transaction
from split.models import Category


class UserExpenseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    owe = serializers.DecimalField(max_digits=20, decimal_places = 2)
    lend = serializers.DecimalField(max_digits=20, decimal_places = 2)


class ExpenseSerializer(serializers.ModelSerializer):
    users = UserExpenseSerializer(many=True)
    categories = serializers.DictField()
    class Meta:
        model = Expense
        fields = ('description', 'categories','total_amount', 'users')

class BalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Balance
        fields = ('amount', 'ower', 'lender', 'expense_id')

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('expense_id', 'user_id', 'owe', 'lend')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'