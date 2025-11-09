from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Book, Author, Category, Member, Loan, Fine
from .forms import BookForm, AuthorForm, CategoryForm

# Dashboard view
def index(request):
    return redirect('dashboard')

def dashboard(request):
    # Calculate statistics
    total_books = Book.objects.count()
    total_members = Member.objects.count()
    active_loans = Loan.objects.filter(return_date__isnull=True).count()
    overdue_loans = Loan.objects.filter(
        return_date__isnull=True,
        due_date__lt=timezone.now().date()
    ).count()
    
    # Recent activities
    recent_loans = Loan.objects.select_related('book', 'member').order_by('-issue_date')[:5]
    recent_returns = Loan.objects.filter(return_date__isnull=False).select_related('book', 'member').order_by('-return_date')[:5]
    
    # Popular books
    popular_books = Book.objects.annotate(
        loan_count=Count('loan')
    ).order_by('-loan_count')[:5]
    
    context = {
        'total_books': total_books,
        'total_members': total_members,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'recent_loans': recent_loans,
        'recent_returns': recent_returns,
        'popular_books': popular_books,
    }
    return render(request, 'library/dashboard.html', context)

# Book views
def book_list(request):
    query = request.GET.get('q')
    category_filter = request.GET.get('category')
    
    books = Book.objects.select_related('author').prefetch_related('category')
    
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(isbn__icontains=query)
        )
    
    if category_filter:
        books = books.filter(category__id=category_filter)
    
    categories = Category.objects.all()
    
    context = {
        'books': books,
        'categories': categories,
        'current_query': query,
        'current_category': category_filter,
    }
    return render(request, 'library/book_list.html', context)

def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    active_loans = Loan.objects.filter(book=book, return_date__isnull=True)
    loan_history = Loan.objects.filter(book=book).select_related('member').order_by('-issue_date')[:10]
    
    context = {
        'book': book,
        'active_loans': active_loans,
        'loan_history': loan_history,
        'is_available': book.available_copies > 0,
    }
    return render(request, 'library/book_detail.html', context)

# Member views
def member_list(request):
    query = request.GET.get('q')
    
    members = Member.objects.all()
    
    if query:
        members = members.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )
    
    # Add loan statistics
    for member in members:
        member.active_loans = Loan.objects.filter(member=member, return_date__isnull=True).count()
        member.total_loans = Loan.objects.filter(member=member).count()
    
    context = {
        'members': members,
        'current_query': query,
    }
    return render(request, 'library/member_list.html', context)

def member_detail(request, pk):
    member = get_object_or_404(Member, pk=pk)
    active_loans = Loan.objects.filter(member=member, return_date__isnull=True).select_related('book')
    loan_history = Loan.objects.filter(member=member).select_related('book').order_by('-issue_date')
    unpaid_fines = Fine.objects.filter(loan__member=member, paid=False)
    
    context = {
        'member': member,
        'active_loans': active_loans,
        'loan_history': loan_history,
        'unpaid_fines': unpaid_fines,
        'total_unpaid_fines': sum(fine.amount for fine in unpaid_fines),
    }
    return render(request, 'library/member_detail.html', context)

# Loan views
def loan_list(request):
    loans = Loan.objects.filter(return_date__isnull=True).select_related('book', 'member').order_by('due_date')
    
    # Mark overdue loans
    today = timezone.now().date()
    for loan in loans:
        loan.is_overdue = loan.due_date < today
        loan.days_overdue = (today - loan.due_date).days if loan.is_overdue else 0
    
    context = {
        'loans': loans,
    }
    return render(request, 'library/loan_list.html', context)

def overdue_loans(request):
    today = timezone.now().date()
    loans = Loan.objects.filter(
        return_date__isnull=True,
        due_date__lt=today
    ).select_related('book', 'member').order_by('due_date')
    
    for loan in loans:
        loan.days_overdue = (today - loan.due_date).days
    
    context = {
        'loans': loans,
    }
    return render(request, 'library/overdue_loans.html', context)

# Author and Category views
def author_list(request):
    authors = Author.objects.annotate(book_count=Count('book')).order_by('name')
    
    context = {
        'authors': authors,
    }
    return render(request, 'library/author_list.html', context)

def category_list(request):
    categories = Category.objects.annotate(book_count=Count('book')).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'library/category_list.html', context)

# Search view
def search(request):
    query = request.GET.get('q')
    results = {}
    
    if query:
        # Search books
        results['books'] = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(isbn__icontains=query)
        ).select_related('author')[:10]
        
        # Search members
        results['members'] = Member.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        )[:10]
        
        # Search authors
        results['authors'] = Author.objects.filter(
            name__icontains=query
        )[:10]
    
    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'library/search_results.html', context)

# Form views
def book_add(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" has been added successfully!')
            return redirect('book_detail', slug=book.slug)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BookForm()
    
    context = {
        'form': form,
        'title': 'Add New Book'
    }
    return render(request, 'library/book_form.html', context)

def member_add(request):
    return render(request, 'library/member_form.html')

def loan_issue(request):
    return render(request, 'library/loan_issue.html')

def loan_return(request):
    return render(request, 'library/loan_return.html')
