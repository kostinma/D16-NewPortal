from apscheduler.schedulers.background import BackgroundScheduler

# register in apps.py:ready()
news_scheduler = BackgroundScheduler()
'''
news_scheduler.add_job(
    id='test send mails',
    func=lambda: print('123'),
    trigger='interval',
    seconds=5,
)
'''