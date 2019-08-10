from django.http import HttpResponse
import simplejson as json

from rest_framework.permissions import AllowAny

from split.models import Expense
from django.db.models import Sum
from split.serializers import ExpenseSerializer
from split.models import Category
from split.serializers import CategorySerializer
from split.models import Balance
from split.models import Transaction

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from django.contrib.auth import login as auth_login

from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, renderer_classes, permission_classes

import logging

logger = logging.getLogger(__name__)


def index(request):
    return HttpResponse("Hello, world. You can answer to a GET request")


def packResponse(status, data={}, message=""):
    content = {'status': "", 'data': data, 'message': message}
    return Response(content, status=status);


class CategoryViewset(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


@api_view(('POST',))
@require_http_methods('POST')
@csrf_exempt
def signup(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        username = request_body["email"]
        password = request_body["password"]
        if username and password:
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(username=username, password=password)
                u.save()
                return packResponse(status=status.HTTP_201_CREATED)
            else:
                return packResponse(status=status.HTTP_403_FORBIDDEN)
        else:
            return packResponse(status=status.HTTP_400_BAD_REQUEST)


@api_view(('POST',))
# @csrf_exempt
@permission_classes((AllowAny,))
def login(request):
    if request.method == 'POST':
        request_body = json.loads(request.body)
        username = request_body["email"]
        password = request_body["password"]
        if username:
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return packResponse(status=status.HTTP_200_OK)
            else:
                logger.debug("entered here")
                return packResponse(status=status.HTTP_401_UNAUTHORIZED)
        else:
            return packResponse(status=status.HTTP_404_NOT_FOUND)


# @login_required
@csrf_exempt
@api_view(('POST','GET',))
def expenses(request):
    logger.debug(request)
    if request.method == 'POST':
        request_body = json.loads(request.body)
        expense = ExpenseSerializer(data=request_body)
        if expense.is_valid():
            post_data = expense.validated_data
            expense = Expense.objects.create(description=post_data["description"],
                                             total_amount=post_data["total_amount"],
                                             category=Category.objects.get(id=post_data["categories"]["id"]))
            expense.save()
            created_id = create_expense(expense, post_data["users"])
            return packResponse(data={"id": created_id}, status=status.HTTP_201_CREATED)
        else:
            print(expense.errors)
            return packResponse(status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'GET':
        return fetch_expenses(request)



def create_expense(expense, data):
    for u in data:
        payment = Transaction.objects.create(expense=Expense.objects.get(id=expense.id),
                                             user=User.objects.get(id=u["id"]), owe=u["owe"], lend=u["lend"])
        payment.save()
        logger.debug(payment)
    add_to_balances(data, expense)
    return expense.id


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


@api_view(('GET',))
def access_expense(request, expense_id):
    user = User.objects.get(id=1)
    # user = request.user
    # if not request.user or not request.user.is_authenticated:
    #     packResponse(status=status.HTTP_401_UNAUTHORIZED)

    # check if user is previleged enough to know about this group
    if request.method == 'GET':
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
        return packResponse(data=data, status=status.HTTP_200_OK)
    elif request.method == "PUT":
        expense = Expense.objects.get(id=expense_id)
        request_body = json.loads(request.body)
        switch = validate_post_request_json(request_body)
        # if switch == ?:
        if request_body["categories"]:
            expense.category = request_body["categories"]["id"]
        if request_body["description"]:
            expense.description = request_body["description"]
        if request_body["users"]:
            Transaction.objects.filter(expense=expense).delete()
            create_expense(request_body["users"])
        return packResponse(status=status.HTTP_200_OK)
    elif request.method == "DELETE":
        e = Expense.objects.get(id=expense_id).update(deleted=1)
        e.save()
        return packResponse(status=status.HTTP_200_OK)


def validate_post_request_json(json):
    return True

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
        return packResponse(data=data, status=status.HTTP_200_OK)

@api_view(('GET',))
def access_balance(request, user_id):
    if request.method == 'GET':
        logged_user = User.objects.get(id=1)
        settle_with = User.objects.get(id=user_id)
        balances = Balance.objects.filter(expense__deleted = 0).filter(
            (Q(ower=logged_user) & Q(lender=settle_with)) | (Q(lender=logged_user) & Q(ower=settle_with)))
        amount = 0
        for b in balances:
            if logged_user == b.ower:
                amount -= b.amount
            else:
                amount += b.amount
    data = \
        {
            "id": user_id,
            "email": settle_with.username,
            "amount": amount
        }
    return packResponse(data=data, status=status.HTTP_200_OK)

@api_view(('GET',))
def fetch_balances(request):
    if request.method == 'GET':
        logged_user = User.objects.get(id=1)
        balances = Balance.objects.filter(expense__deleted = 0).filter(Q(ower=logged_user) | Q(lender=logged_user))
        amounts = {}
        for b in balances:
            logger.debug(str(b.ower) + str(b.lender) + str(b.amount))
            if b.ower == logged_user:
                if b.lender in amounts:
                    amounts[b.lender] -= b.amount
                else:
                    amounts[b.lender] = -b.amount
            elif b.lender == logged_user:
                if b.ower in amounts:
                    amounts[b.ower] += b.amount
                else:
                    amounts[b.ower] = b.amount
            else:
                logger.debug("shouldnt enter")
        bal_arr = []
        for k in amounts:
            bal_arr.append(
                {
                    "id": k.id,
                    "email": k.username,
                    "amount": amounts[k]
                }
            )
        data = \
            {
                "balances": bal_arr
            }
        return packResponse(data=data, status=status.HTTP_200_OK)

@api_view(('POST',))
def settle_balance(request):
    if request.method == 'POST':
        logged_user = User.objects.get(id=1)
        request_body = json.loads(request.body)
        settle_with = request_body["users"]["id"]
        balances = Balance.objects.filter(
            (Q(ower=logged_user) & Q(lender=settle_with)) | (Q(lender=logged_user) & Q(ower=settle_with)))
        amount = 0
        for b in balances:
            if logged_user == b.ower:
                amount -= b.amount
            else:
                amount += b.amount

        if amount == 0:
            return packResponse(status=status.HTTP_403_FORBIDDEN)
        if amount > 0:
            e = Expense.objects.create(description="settlement", category_id=1, total_amount=amount)
            data = \
                [
                    {
                        "id": logged_user.id,
                        "owe": amount,
                        "lend": 0
                    },
                    {
                        "id": settle_with,
                        "owe": 0,
                        "lend": amount
                    }
                ]
        else:
            e = Expense.objects.create(description="settlement", category_id=1, total_amount=-amount)
            data = \
                [
                    {
                        "id": logged_user.id,
                        "owe": 0,
                        "lend": -amount
                    },
                    {
                        "id": settle_with,
                        "owe": -amount,
                        "lend": 0
                    }
                ]
        created_id = create_expense(e, data)
        return packResponse(data={"id": created_id}, status=status.HTTP_201_CREATED)

@api_view(('GET',))
def profile(request):
    if request.method == 'GET':
        logged_user = User.objects.get(id=1)
        lent = Balance.objects.filter(lender=logged_user).aggregate(Sum('amount'))['amount__sum']
        owed = Balance.objects.filter(ower=logged_user).aggregate(Sum('amount'))['amount__sum']
        logger.debug(lent)
        data = \
            {
                "outstanding_amount": lent - owed
            }
        return packResponse(data = data, status=status.HTTP_200_OK)
