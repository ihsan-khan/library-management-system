from django import forms
from django.utils.text import slugify
from .models import Book, Author, Category


class BookForm(forms.ModelForm):
    # Override the author field to show a dropdown with existing authors
    author = forms.ModelChoiceField(
        queryset=Author.objects.all(),
        empty_label="Select an Author",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_author'
        })
    )
    
    # Override categories field for better display
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label="Categories"
    )
    
    # Add a field for creating new author if needed
    new_author_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new author name...'
        }),
        label="Or Add New Author"
    )
    
    new_author_biography = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Brief biography of the author (optional)...'
        }),
        label="Author Biography"
    )
    
    # Add field for creating new categories
    new_categories = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new categories separated by commas...'
        }),
        label="Or Add New Categories",
        help_text="Enter multiple categories separated by commas"
    )

    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'category', 'publisher', 'published_date', 'total_copies', 'available_copies']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter book title...'
            }),
            'isbn': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter ISBN (10 or 13 digits)...',
                'pattern': '[0-9X-]+',
                'title': 'ISBN should contain only numbers, X, and hyphens'
            }),
            'publisher': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter publisher name...'
            }),
            'published_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Number of total copies...'
            }),
            'available_copies': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Number of available copies...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make available_copies default to total_copies value
        if 'total_copies' in self.data:
            try:
                total = int(self.data['total_copies'])
                if not self.data.get('available_copies'):
                    self.fields['available_copies'].widget.attrs['placeholder'] = f'Default: {total}'
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        total_copies = cleaned_data.get('total_copies')
        available_copies = cleaned_data.get('available_copies')
        author = cleaned_data.get('author')
        new_author_name = cleaned_data.get('new_author_name')

        # Validate that either existing author is selected or new author name is provided
        if not author and not new_author_name:
            raise forms.ValidationError("Please select an existing author or provide a new author name.")
        
        if author and new_author_name:
            raise forms.ValidationError("Please select either an existing author OR create a new one, not both.")

        # Validate available copies doesn't exceed total copies
        if total_copies and available_copies is not None:
            if available_copies > total_copies:
                raise forms.ValidationError("Available copies cannot exceed total copies.")
        
        # If available_copies is not provided, set it to total_copies
        if total_copies and available_copies is None:
            cleaned_data['available_copies'] = total_copies

        return cleaned_data

    def clean_isbn(self):
        isbn = self.cleaned_data['isbn']
        # Remove hyphens and spaces for validation
        isbn_clean = isbn.replace('-', '').replace(' ', '')
        
        # Check if ISBN is valid length (10 or 13 digits, possibly with X at end for ISBN-10)
        if not (len(isbn_clean) in [10, 13] and (isbn_clean[:-1].isdigit() or isbn_clean.isdigit())):
            if len(isbn_clean) == 10 and isbn_clean[-1].upper() == 'X':
                pass  # Valid ISBN-10 with X
            else:
                raise forms.ValidationError("ISBN must be 10 or 13 digits long.")
        
        return isbn

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle new author creation
        new_author_name = self.cleaned_data.get('new_author_name')
        if new_author_name:
            author, created = Author.objects.get_or_create(
                name=new_author_name,
                defaults={'biography': self.cleaned_data.get('new_author_biography', '')}
            )
            instance.author = author
        
        # Generate slug from title
        if not instance.slug:
            base_slug = slugify(instance.title)
            slug = base_slug
            counter = 1
            while Book.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            instance.slug = slug
        
        if commit:
            instance.save()
            
            # Handle new categories
            new_categories = self.cleaned_data.get('new_categories')
            if new_categories:
                category_names = [name.strip() for name in new_categories.split(',') if name.strip()]
                for category_name in category_names:
                    category, created = Category.objects.get_or_create(name=category_name)
                    instance.category.add(category)
            
            # Save many-to-many relationships
            self.save_m2m()
        
        return instance


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'biography']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter author name...'
            }),
            'biography': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter author biography...'
            })
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name...'
            })
        }