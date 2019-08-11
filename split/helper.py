import simplejson as json
from split.models import Expense
from split.models import Balance
from split.models import Transaction

from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


"""
Gets all expenses
"""
def fetch_expenses(request):
    if request.method == 'GET':
        user = User.objects.get(id=1)
        expenses = [Expense.objects.filter(deleted = 0).get(id = t.expense.id) for t in Transaction.objects.filter(user=user)]
        count = len(expenses)
        expense_arr = []
        for e in expenses:
            transactions = Transaction.objects.filter(expense=e)
            users = []
            for t in transactions:
                users.append({"id": t.user.id, "owe": t.owe, "lend": t.lend})
            expense_arr.append(
                {
                    "id": e.id,
                    "categories": {
                        "id": e.category.id
                    },
                    "description": e.description,
                    "total_amount": e.total_amount,
                    "users": users
                }
            )
        data = \
            {
                "count": count,
                "expenses": expense_arr
            }
        return data

"""
Creates expense and transactions, adds it to balance table
"""
def create_expense(expense, data):
    for u in data:
        payment = Transaction.objects.create(expense=Expense.objects.get(id=expense.id),
                                             user=User.objects.get(id=u["id"]), owe=u["owe"], lend=u["lend"])
        payment.save()
        logger.debug(payment)
    add_to_balances(data, expense)
    return expense.id

"""
Adds balances corresponding to an expense to balance table
"""
def add_to_balances(user_payments, expense):
    lenders = {}
    owers = {}
    logger.debug(json.dumps(user_payments))
    for p in user_payments:
        logger.debug(p)
        if p['owe'] > p['lend']:
            owers[p['id']] = p['owe'] - p['lend']
        elif p['owe'] < p['lend']:
            lenders[p['id']] = p['lend'] - p['owe']

    O = list(owers)
    L = list(lenders)
    o = l = 0
    while (o < len(O)) and (l < len(L)):
        if owers[O[o]] < lenders[L[l]]:
            b = Balance.objects.create(ower_id=O[o], lender_id=L[l], amount=owers[O[o]], expense=expense)
            b.save()
            lenders[L[l]] -= owers[O[o]]
            o += 1
        else:
            b = Balance.objects.create(ower_id=O[o], lender_id=L[l], amount=lenders[L[l]], expense=expense)
            b.save()
            owers[O[o]] -= lenders[L[l]]
            l += 1

def pack_data_for_settlement(ower, lender, amount):
    data = \
        [
        {
            "id": ower,
            "owe": amount,
            "lend": 0
        },
        {
            "id": lender,
            "owe": 0,
            "lend": amount
        }
    ]
    return data

def get_specific_expense(expense_id):
    expense = Expense.objects.get(id=expense_id)
    transactions = Transaction.objects.filter(expense=expense)
    users = []
    for t in transactions:
        users.append({"id": t.user.id, "owe": t.owe, "lend": t.lend})
    data = \
        {
            "expenses":
                {
                    "id": expense.id,
                    "categories": {
                        "id": expense.category.id
                    },
                    "description": expense.description,
                    "total_amount": expense.total_amount,
                    "users": users
                }
        }
    return data

"""
Calculates balances of the logged user against peers
"""
def calculate_balances(balances, logged_user):
    amounts = {}
    for balance in balances:
        if balance.ower == logged_user:
            if balance.lender in amounts:
                amounts[balance.lender] -= balance.amount
            else:
                amounts[balance.lender] = -balance.amount
        elif balance.lender == logged_user:
            if balance.ower in amounts:
                amounts[balance.ower] += balance.amount
            else:
                amounts[balance.ower] = balance.amount
    return amounts