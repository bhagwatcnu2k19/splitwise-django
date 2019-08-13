from django.conf.urls import url
from django.urls import path, include

from . import views
from django.views.decorators.csrf import csrf_exempt

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'category', views.CategoryViewset)


urlpatterns = [
    path('helloworld', views.index, name='index'),
    url(r'^', include(router.urls)),

    path('expenses/', views.expenses, name='expenses'),
    path('expenses/<int:expense_id>/', views.access_expense, name='access_expense'),

    path('users/<int:user_id>/balances/', views.access_balance, name='access_balance'),
    path('balances/', views.fetch_balances, name='fetch_balances'),
    path('settle/', views.settle_balance, name='settle'),

    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', views.login, name='login'),

    path('profile/', views.profile, name='profile'),

    path('report/', views.report, name='report'),
    path('server_failed/', views.server_failed, name='failure')


]
