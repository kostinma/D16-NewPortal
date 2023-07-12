
# В первую очередь мы импортируем библиотеку для взаимодействия с
# операционной системой и саму библиотеку Celery.
import os
from celery import Celery
from celery.schedules import crontab


# Второй строчкой мы связываем настройки Django с настройками Celery через переменную окружения.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewsPortal.settings')

# Далее мы создаём экземпляр приложения Celery и устанавливаем для него файл конфигурации.
# Мы также указываем пространство имён, чтобы Celery сам находил все необходимые настройки в
# общем конфигурационном файле settings.py. Он их будет искать по шаблону «CELERY_***».
app = Celery('NewsPortal')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Последней строчкой мы указываем Celery автоматически искать задания в файлах
# tasks.py
# каждого приложения проекта.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'past_week_posts_notifications_on_monday_at_8am': {
        'task': 'news.tasks.task_notify_about_last_week_posts',
        # 'schedule': 30, # every 30 seconds, use for tests
        # 'schedule': crontab(minute='*/1'), # use for tests
        'schedule': crontab(hour=8, minute=0, day_of_week='monday'),
        # 'args': (5,), # arguments to task function
    }
}

'''
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
(venv) PS C:...> python .\manage.py shell
>>> from NewsPortal.celery import debug_task
>>> debug_task.delay()                               
<AsyncResult: a8a9b919-5927-4bff-be7d-3a9685ba2c68>
>>> 
'''
