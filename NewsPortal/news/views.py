from datetime import datetime
from pprint import pprint
import time

from django.conf import settings

from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.cache import cache
from django.template.loader import render_to_string  # generate html as text (?)

from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)

from .models import Post, Category
from .filters import SearchPostFilter
from .forms import PostForm
from .utils_email import notify_about_new_post, is_email_valid
from .tasks import task_notify_about_new_post

# simple celery test, .tasks.py
# from .tasks import test_celery_print_hello
from django.http import HttpResponse


class TestCeleryView(View):
    def get(self, request):
        # test_celery_print_hello.delay()
        return HttpResponse('Hello!')


class PostList(ListView):
    model = Post
    # ordering = 'title'
    ordering = 'time_in'
    # Or, alternatively
    # queryset = Post.objects.order_by('time_in')
    template_name = 'news.html'
    context_object_name = 'news'
    paginate_by = 2

    '''
    # test 1, simple email
    send_mail(
        subject='test e-mail',
        message='This is a test',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[''],
    )
    '''

    # mail_admins() # similar to send_mail
    # Add to settings.py:
    # ADMINS = [...]
    # ERVER_EMAIL='...'
    # ame to send to managers: MANAGERS

    '''
    class WhatIsIt:
        field_1 = 'Hmm 1 1 1'
        field_2 = 'Hmmmmm 2 2 2'
        field_3 = 17

    test_stuff = WhatIsIt()

    # test 2, html email
    html_content = render_to_string(
        'test_html_email.html',
        {
            'zzzzz': test_stuff,
        }
    )

    msg = EmailMultiAlternatives(
        subject='HTML version of email',
        body='This is a test of HTML email', # will be replaced later
        from_email=settings.DEFAULT_FROM_EMAIL, 
        to=[''],
    )
    msg.attach_alternative(html_content, "text/html")  # add html
    msg.send()
    '''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()
        # pprint(context)
        return context

    def get_object(self, *args, **kwargs):
        obj = cache.get(f'post-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)
        return obj


class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'

    def get_object(self, *args, **kwargs):
        obj = cache.get(f'post-{self.kwargs["pk"]}', None)
        if not obj:
            obj = super().get_object(queryset=self.queryset)
            cache.set(f'post-{self.kwargs["pk"]}', obj)
        return obj


class SearchPostList(ListView):
    model = Post
    # ordering = 'title'
    ordering = 'time_in'
    # Or, alternatively
    # queryset = Post.objects.order_by('time_in')
    template_name = 'news_search.html'
    context_object_name = 'news_search'
    paginate_by = 2

    # redefine function of getting list of Posts
    # SearchPostFilter is in filters.py
    def get_queryset(self):
        # get request
        queryset = super().get_queryset()

        # self.request.Get has an object of class QueryDict
        # keep filtration in class object so that will add it into context
        # and use in template.
        # SearchPostFilter is found in filters.py
        self.filterset = SearchPostFilter(self.request.GET, queryset)

        # return filtered list
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()

        # self.get_queryset(self) created an object of filtered list
        context['filterset'] = self.filterset

        # pprint(context)
        return context

# added LoginRequiredMixin
class PostCreate(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = ('news.add_post')
    model = Post
    form_class = PostForm
    template_name = 'post_create.html'

    def form_valid(self, form):
        post = form.save(commit=False)
        if self.request.method == 'POST':
            path_info = self.request.META['PATH_INFO']
            if path_info == '/news/create/':
                post.post_type = Post.POSTS[1]
                # Post.POSTS = ['article', 'news_piece']
            elif path_info == '/article/create/':
                post.post_type = Post.POSTS[0]
                # Post.POSTS = ['article', 'news_piece']
            else:
                raise ValidationError(
                    'PostCreate.from_valid(): Wrong url.'
                )

            post.save()

            # Sending email directly from view does not work well.
            # It is not enough time to save categories in db.
            # The list of categories for post comes back empty.
            # Using sleep() does not work also - the whole system sleeps.
            # Must use a different approach. For example, create a threat
            # and send out emails in background after waiting for a certain
            # period of time. Asynchroneously.
            # post=Post.objects.get(pk=post.pk) # just to read back from db
            # notify_about_new_post(post)
            # ->
            # Use signals.py instead

            # celery+redis, or can use signals instead:
            # signals.py:@receiver(...)notify_post_added_or_category_changed(...),
            # which right now is commented out
            # task_notify_about_new_post.delay(post.pk)
            task_notify_about_new_post.apply_async([post.pk], countdown=10)

        return super().form_valid(form)


class PostDelete(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('news_search')


class PostUpdate(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = ('news.change_post')
    model = Post
    form_class = PostForm
    template_name = 'post_edit.html'


class CategoryList(ListView):
    model = Post
    template_name = 'category.html'
    ordering = 'name'
    context_object_name = 'categories'

    def get_queryset(self):
        # find first category in the list for this post
        self.category = get_object_or_404(Category, id=self.kwargs['pk'])
        # find all posts with this category
        queryset = Post.objects.filter(category=self.category).order_by('title')
        #queryset = Post.objects.filter(
        #    category=
        #).order_by('title')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_not_subscriber'] = self.request.user not in self.category.subscribers.all()
        context['category'] = self.category
        return context


@login_required
def subscribe(request, pk):
    user = request.user
    category = Category.objects.get(id=pk)
    category.subscribers.add(user)

    if is_email_valid(user.email):
        send_mail(
            subject=f'New subscription {category.name} added',
            message=f'Dear {user.username}, Category {category.name} was added to your subscription list.',
            from_email='noreply@example.com',
            recipient_list=[f'{user.email}'],
        )

    message = f'You have subscribed for the category {category.name}'

    # Return HttpResponse object
    return render(request, 'subscribe.html', {'category': category, 'message': message})


# End of file
