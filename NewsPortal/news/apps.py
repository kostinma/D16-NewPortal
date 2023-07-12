from django.apps import AppConfig

# from django.core.signals import setting_changed, request_finished

'''
# def my_callback(sender, **kwargs):
#    print('Settings changed!')
'''

class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    # Connect app news to @receiver in signals.py
    # When config works, all functions from signals.py will imported.
    def ready(self):
        import news.signals

        '''
        # appname.signals
        # used @receiver instead of connect()
        '''

        '''
        # setting_changed.connect(my_callback) # register a receiver
        # or
        # from .import signals
        # request_finished.connect(signals.my_callback)
        '''

        '''
        # work with django-apscheduler
        # periodic tasks
        from .tasks import test_send_mails
        from .scheduler import news_scheduler
        print('started') # will run it twice - run test of ready() first (tests), then run server
        # python manager.py runserver --noreload will run it once
        # Changes will not be uploaded to server with --noreload, must restart server manually - bad
        news_scheduler.add_job(
            id='test send mails',
            func=test_send_mails,
            trigger='interval',
            seconds=10,
        )
        news_scheduler.start()

        # Can also run scheduler from views.py. It this case we can run it dynamically.
        '''
