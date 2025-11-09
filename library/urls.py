from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Book management
    path('books/', views.book_list, name='book_list'),
    path('books/add/', views.book_add, name='book_add'),
    path('books/<slug:slug>/', views.book_detail, name='book_detail'),
    
    # Member management
    path('members/', views.member_list, name='member_list'),
    path('members/add/', views.member_add, name='member_add'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
    
    # Loan management
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/overdue/', views.overdue_loans, name='overdue_loans'),
    path('loans/issue/', views.loan_issue, name='loan_issue'),
    path('loans/return/', views.loan_return, name='loan_return'),
    
    # Authors and Categories
    path('authors/', views.author_list, name='author_list'),
    path('categories/', views.category_list, name='category_list'),
    
    # Search
    path('search/', views.search, name='search'),
]