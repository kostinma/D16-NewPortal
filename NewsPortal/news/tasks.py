import datetime

import time
from celery import shared_task

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Post, Category
from .utils_email import notify_about_new_post
from .management.commands.runapscheduler import my_job

'''
Tasks performed in background
'''

def test_send_mails():
    print('test_send_mails: hello from background task')

'''
Simple test of celery
views.TestCeleryView.get().test_celery_print_hello()
'''
'''
@shared_task
def test_celery_print_hello():
    time.sleep(10)
    print('Hello world!')
'''

# send messages to subscribers of categories about a new post
@shared_task
def task_notify_about_new_post(post_pk):
    post = Post.objects.get(pk=post_pk)
    notify_about_new_post(post) # reusing code written for signals


# send lists of last week posts to subscribers


@shared_task
def task_notify_about_last_week_posts():
    '''
        celery -A PROJECT worker -l INFO -E --pool=solo
        and
        celery -A PROJECT beat -l INFO
    '''
    print('task_notify_about_last_week_posts: weekly notification out')
    # .management.commands.runapscheduler.my_job()
    my_job()  # reuse already written function used with the command runapsheduler.py

