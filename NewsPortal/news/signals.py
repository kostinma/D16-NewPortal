from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import m2m_changed
# from django.dispatch import receiver
from django.template.loader import render_to_string

from .models import PostCategory

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.signals import request_finished
from django.core.mail import mail_managers

from .utils_email import notify_about_new_post


'''
# 1
def notify_managers_appointment(
        sender,    # model (Appointment), mandatory
        instance,  # not mandatory, object of saved model
        created,   # if instance is in db, not mandatory
        **kwargs   # mandatory
):
    mail_managers(
        subject='f{instance.client_name} {instance.date.strftime("%d %m %Y")}',
        message=instance.message
    )

post_save.connect(notify_managers_appointment, sender=Appointment)

# 2 instead of post_save use decorator
@receiver(post_save, sender=Appointment)
def notify_managers_appointment(
        sender,    # model (Appointment)
        instance,
        created,   # if instance is in db
        **kwargs):
    if created:
        subject = f'{instance.client_name} {instance.date.strftime("%d %m %Y")}'
    else:
        subject = f'Appointment changed for {instance.client_name} {instance.date.strftime("%d %m %Y")}'

    mail_managers(
        subject=subject,
        message=instance.message,
    )
'''



'''
Сигналы — это события, которые происходят в нашем приложении. 
Например, завершение каждого запроса — это событие, сохранение модели в БД — событие, 
запись объекта модели в БД и т. д., и т. п.
'''

'''
Instead of post_save use m2m_changed (Many2ManyField). 
This way, notifications will be sent out not only when a new Post is added, 
but also when Post category is updated. 
This may also help with the issue of delay of Category update - 
when a new Post is saved into db, Post.category is taking time to update. 
This was an issue with sending notification directly from views.CreatePost. 
'''
@receiver(
    m2m_changed, # a signal or a list of signals to connect the function to, used through=...
    sender=PostCategory # The intermediate model class describing the ManyToManyField.
    # This class is automatically created when a many-to-many field is defined;
    # you can access it using the 'through' attribute on the many-to-many field.
)
def notify_post_added_or_category_changed(
        sender,   # in this case model class of ManyToManyField
        instance, # The instance whose many-to-many relation is updated.
        # This can be an instance of the sender, or of the class the ManyToManyField is related to (Post).
        **kwargs  #
):
    # print('notify_post_added_or_category_changed: ', type(instance))
    # notify_post_added_or_category_changed: <class 'news.models.Post'>
    if kwargs['action'] == 'post_add':    # after one or more objects were added to the relation
        # notify_about_new_post(instance)  - use celery/redis/tasks instead
        pass
