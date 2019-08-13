from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

import boto3
from celery import Celery
from celery import shared_task
import simplejson as json
from split.models import Expense
from django.db.models import Sum, Count
from split.serializers import ExpenseSerializer
from split.models import Category
from split.serializers import CategorySerializer
from split.models import Balance
from split.models import Transaction

from django.contrib.auth.models import User
import shutil
import django
from django.core.mail import EmailMessage
import glob


# logger = logging.getLogger(__name__)
@shared_task
def top5_categories():
    top5_file = open('top5_categories.txt', 'w')
    top5_categories = Expense.objects.all().values('category_id').annotate(total=Sum('total_amount')).order_by('-total')[:5]
    top5_file.write("Top 5 categories are\n")
    for cat in top5_categories:
        top5_file.write(str(cat))
        top5_file.write('\n')
    top5_file.close()
    return "Query 1 completed."

@shared_task
def monthly_category_wise(user_id):
    monthly_file = open('monthly_category_wise.txt', 'w')
    expenses = [e['expense_id'] for e in Transaction.objects.filter(user_id=user_id).values('expense_id')]
    last_six_months = range(41,48)
    monthly_file.write("Monthly category-wise expenses for the logged-in user are as follows : \n")
    for month in last_six_months:
        monthly_file.write("Expenses for month number " + str(month) + "is \n")
        monthly_expenses = Expense.objects.filter(id__in=expenses).filter(month_number=month).values('category_id').annotate(total=Sum('total_amount'))
        for cat in monthly_expenses:
            monthly_file.write(str(cat))
            monthly_file.write('\n')
    monthly_file.write("\n\n")
    monthly_file.close()
    return "Query 2 completed."

@shared_task
def top_lender():
    top_lender_file = open('top_lender.txt', 'w')
    lender = Transaction.objects.all().values('user_id').annotate(total=Sum('lend')).order_by('-lend')[:1]
    top_lender_file.write("Top lender has 'email"  + str(lender[0]['user_id']) + "' and total lent amount is " + str(lender[0]['total']))
    top_lender_file.write('\n')
    top_lender_file.close()
    return "Query 3 completed."

@shared_task
def top_ower():
    top_ower_file = open('top_ower.txt', 'w')
    ower = Transaction.objects.all().values('user_id').annotate(total=Sum('owe')).order_by('-total')[:1]
    # print(ower[0]['user_id'])
    top_ower_file.write("Top ower has email 'email" + str(ower[0]['user_id']) + "' and total owed amount is " + str(ower[0]['total']))
    top_ower_file.write('\n')
    top_ower_file.close()
    return "Query 4 completed."

@shared_task
def most_active_users():
    most_active_file = open('most_active_users', 'w')
    active_users = Transaction.objects.all().values('user_id').annotate(total=Count('user_id')).order_by('-total')[:5]
    most_active_file.write("Top 5 most active users are the following :-\n")
    for cat in active_users:
        most_active_file.write("email" + str(cat['user_id']))
        most_active_file.write('\n')
    most_active_file.close()
    return "Query 5 completed."


@shared_task
def email_report():
    # outfile = open('final_report.txt', 'wb')
    data = ""
    for filename in glob.glob('*.txt'):
        with open(filename, 'rb') as readfile:
            data += str(readfile.read())

    email = EmailMessage(
        'Hello',
        'Body goes here',
        'bhagwat.aditya@codenation.co.in',
        ['bhagwat.aditya@codenation.co.in'],
    )
    email.attach('report.txt', data , 'text/plain')
    email.send()




