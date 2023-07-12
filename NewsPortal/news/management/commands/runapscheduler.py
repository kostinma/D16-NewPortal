import datetime
import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from ...models import Post, Category

from news.utils_email import is_email_valid


logger = logging.getLogger(__name__)


def my_job():
    print('my_job: Hello from job!')

    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=7)
    # print('my_job: cutoff time: ', cutoff_time)

    recent_posts = Post.objects.filter(time_in__gte = cutoff_time)
    # print('my_job: ', recent_posts)

    # All unique names of categories in selected posts
    # flat=True, get [...] instead of [(,)...]
    category_names = set(recent_posts.values_list('category__name', flat=True))
    # print('my_job: categories: ', category_names)

    # Identify all the unique subscribers that are subscribed to these categories above.
    # Must use set() because some subscribers may be duplicated if subscribed to more than one category.
    unique_subscribers = set(
         Category.objects.filter(name__in=category_names).values_list(
             'subscribers__pk',
             'subscribers__username',
             'subscribers__email',
             flat=False
         )
     )

    # print('my_job: type(unique_subscribers): ', type(unique_subscribers))
    # my_job: type(unique_subscribers): <class 'set'>

    # print('my_job: unique_subscribers: ', unique_subscribers)

    # print('my_job: : get_absolute_url: ', Post.objects.get(id=1).get_absolute_url())

    # We will generate unique email for each user.
    # We cannot use list of emails in message, because each user has unique subscription.
    # An email will contain a list of recent articles in categories this particular user
    # is subscribed for. This is the reason for unique email body.
    # Therefore, it is only possible to send one email at a time.

    for one_s in unique_subscribers:
        # print(one_s[0], one_s[1], one_s[2])

        if is_email_valid(one_s[2]):
            # print('my_job: found valid email: ', one_s[2])

            # Find a unique set of posts this person is subscribed for
            posts = recent_posts.filter(category__subscribers__username=one_s[1]).distinct()
            # print('+++++++++++++++++++++++++++++')
            # print(one_s[0], one_s[1], one_s[2])
            # print(type(posts))
            # print(posts)
            # print('------------------------------')

            html_content = render_to_string(
                'weekly_posts.html',
                {
                    'user_name': str(one_s[1]),
                    'site_URL': settings.SITE_URL,
                    'posts': posts,
                }
            )

            email_list = []
            email_list.append(one_s[2])

            msg = EmailMultiAlternatives(
                subject='News Posted Last Week',
                body='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=email_list,  # cannot be a list, unique content tailored to this one user
            )

            msg.attach_alternative(html_content, 'text/html')
            msg.send()


def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        # BlockingScheduler runs in a separate thread.
        # Similar to Background. Could use Background too (?).
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            my_job,
            # trigger=CronTrigger(day_of_week="mon", hour="12", minute="00"),
            trigger=CronTrigger(second="*/10"),
            # CronTrigger is similar to interval
            id="my_job",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Added job 'my_job'.")

        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(
                day_of_week="tue", hour="2", minute="11"
            ),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "Added weekly job: 'delete_old_job_executions'."
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")

