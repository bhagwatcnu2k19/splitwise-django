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

from rest_framework import viewsets
from django.contrib.auth import login as auth_login

from django.db.models import Q

from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, permission_classes

from split.helper import *

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

"""
Create an expense
"""
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
        data = fetch_expenses(request)
        return packResponse(data=data, status=status.HTTP_200_OK)

"""
Get, modify or delete a specific expense 
"""
@api_view(('GET','PUT', 'DELETE'))
def access_expense(request, expense_id):
    user = request.user
    if not user or not user.is_authenticated:
        packResponse(status=status.HTTP_401_UNAUTHORIZED)
    if request.method == 'GET':
        data = get_specific_expense(expense_id)
        return packResponse(data=data, status=status.HTTP_200_OK)
    elif request.method == "PUT":
        request_body = json.loads(request.body)
        expense = Expense.objects.get(id=expense_id)
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

"""
Get outstanding balance against a particular user
"""
@api_view(('GET',))
def access_balance(request, user_id):
    if request.method == 'GET':
        logged_user = request.user
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

"""
Get balances against all users that you had expenses with
"""
@api_view(('GET',))
def fetch_balances(request):
    if request.method == 'GET':
        logged_user = request.user
        balance_objects = Balance.objects.filter(expense__deleted = 0).filter(Q(ower=logged_user) | Q(lender=logged_user))
        final_balances = calculate_balances(balance_objects)
        balance_array = []
        for ower in final_balances:
            balance_array.append(
                {
                    "id": ower.id,
                    "email": ower.username,
                    "amount": final_balances[ower]
                }
            )
        data = \
            {
                "balances": balance_array
            }
        return packResponse(data=data, status=status.HTTP_200_OK)

"""
Settle outstanding balances against a specified user. First calculates this balance then creates a request to settle it
"""
@api_view(('POST',))
def settle_balance(request):
    if request.method == 'POST':
        logged_user = request.user
        request_body = json.loads(request.body)
        settle_with = request_body["users"]["id"]
        balances = Balance.objects.filter(
            (Q(ower=logged_user) & Q(lender=settle_with)) | (Q(lender=logged_user) & Q(ower=settle_with)))
        amount = 0
        for balance in balances:
            if logged_user == balance.ower:
                amount -= balance.amount
            else:
                amount += balance.amount

        if amount == 0:
            return packResponse(status=status.HTTP_403_FORBIDDEN)
        if amount > 0:
            e = Expense.objects.create(description="settlement", category_id=1, total_amount=amount)
            data = pack_data_for_settlement(logged_user.id, settle_with, amount)
        else:
            e = Expense.objects.create(description="settlement", category_id=1, total_amount=-amount)
            data = pack_data_for_settlement(settle_with, logged_user.id, -amount)
        created_id = create_expense(e, data)
        return packResponse(data={"id": created_id}, status=status.HTTP_201_CREATED)


"""Get total outstanding balance taking all users into account"""
@api_view(('GET',))
def profile(request):
    if request.method == 'GET':
        logged_user = request.user
        lent = Balance.objects.filter(lender=logged_user).aggregate(Sum('amount'))['amount__sum']
        owed = Balance.objects.filter(ower=logged_user).aggregate(Sum('amount'))['amount__sum']
        logger.debug(lent)
        data = \
            {
                "outstanding_amount": lent - owed
            }
        return packResponse(data = data, status=status.HTTP_200_OK)
