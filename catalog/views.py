from django.shortcuts import render, get_object_or_404

from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.backends import ModelBackend

from django.core.exceptions import PermissionDenied

from django.http import HttpResponseRedirect, HttpRequest

from django.urls import reverse, reverse_lazy

from .forms import RenewBookForm
from .models import Book, Author, BookInstance, Genre, Language

import datetime


# Create your views here.

def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()  # Метод 'all()' применен по умолчанию.
    num_genre = Genre.objects.count()
    num_lang = Language.objects.count()

    key_word = 'dry'
    num_book_selection = Book.objects.filter(title__icontains = key_word).count()

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    # Отрисовка HTML-шаблона index.html с данными внутри
    # переменной контекста context
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances,
                 'num_instances_available': num_instances_available, 'num_authors': num_authors,
                 'num_genre': num_genre, 'num_book_selection': num_book_selection, 'key_word': key_word,
                 'num_lang': num_lang, 'num_visits':num_visits},
    )


class BookListView(generic.ListView, LoginRequiredMixin):
    permission_required = 'catalog.can_mark_returned'

    model = Book
    paginate_by = 5

class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView, LoginRequiredMixin):
    permission_required = 'catalog.can_mark_returned'

    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to current user.
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 5

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class AllLoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):

    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_all_borrowed_user.html'
    paginate_by = 5

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')



@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


# Author redaction

class AuthorCreate(CreateView):
    model = Author
    fields = '__all__'
    initial={'date_of_death':'12/10/2016',}

    def get(self, request, *args, **kwargs):
        self.object = None
        if not request.user.has_perm('catalog.can_mark_returned'):
            return HttpResponseRedirect(reverse('authors') )

        return render(request, 'catalog/author_form.html', FormMixin.get_context_data(self, **kwargs))

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

    def get(self, request, *args, **kwargs):
        self.object = SingleObjectMixin.get_object(self)
        if not request.user.has_perm('catalog.can_mark_returned'):
            return HttpResponseRedirect(reverse('authors') )

        return render(request, 'catalog/author_form.html', FormMixin.get_context_data(self, **kwargs))

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')

    def get(self, request, *args, **kwargs):
        self.object = SingleObjectMixin.get_object(self)
        if not request.user.has_perm('catalog.can_mark_returned'):
            return HttpResponseRedirect(reverse('authors') )

        return render(request, 'catalog/author_confirm_delete.html', SingleObjectMixin.get_context_data(self, **kwargs))


# Book redaction

class BookCreate(CreateView):
    model = Book
    fields = '__all__'

    def get(self, request, *args, **kwargs):
        self.object = None
        if not request.user.has_perm('catalog.can_mark_returned'):
            return HttpResponseRedirect(reverse('books') )

        return render(request, 'catalog/book_form.html', FormMixin.get_context_data(self, **kwargs))

class BookUpdate(UpdateView):
    model = Book
    fields = ['first_name','last_name','date_of_birth','date_of_death']

    def get(self, request, *args, **kwargs):
        self.object = SingleObjectMixin.get_object(self)
        if not request.user.has_perm('catalog.can_mark_returned'):
            return HttpResponseRedirect(reverse('books') )

        return render(request, 'catalog/book_form.html', FormMixin.get_context_data(self, **kwargs))

class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('books')

    def get(self, request, *args, **kwargs):
        self.object = SingleObjectMixin.get_object(self)
        if not request.user.has_perm('catalog.can_mark_returned'):
            return HttpResponseRedirect(reverse('books') )

        return render(request, 'catalog/book_confirm_delete.html', SingleObjectMixin.get_context_data(self, **kwargs))
