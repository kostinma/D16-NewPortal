from pprint import pprint

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Post


def is_email_valid(email: str) -> bool:
    try:
        validate_email(email)
    except ValidationError as e:
        # print("bad email, details:", e)
        return False
    else:
        # print("good email")
        return True


def notify_about_new_post_subscribers(
        post: Post,
        html_template_name: str,
        category_name: str,
        salutation: str,
        # salutation is needed to personalize email. Can be general 'friend'.
        # Or it can be a user name. It this case, however, make sure there are only
        # emails associated with this user in the email_list below.
        email_list: [str],
) -> None:
    '''
    print('From notify_about_new_post_subscribers:')
    print('++++++++++++++++++++++')
    print(f'HTML template: {html_template_name}')
    print(f'Category name: {category_name}')
    print(f'Salutaion: {salutation}')
    print(f'Email: {email_list[0]}')
    print('----------------------')
    '''

    html_content = render_to_string(
        html_template_name,
        {
            'post_title'    : post.title,
            'post_body'     : post.body,
            'post_link'     : f'{settings.SITE_URL}/news/{post.pk}',
            'category_name' : category_name,
            'salutation'    : salutation,
        }
    )

    msg = EmailMultiAlternatives(
        subject = post.title,
        body = '',
        from_email = settings.DEFAULT_FROM_EMAIL,
        to = email_list,
    )

    msg.attach_alternative(html_content, "text/html")  # add html
    msg.send()


def notify_about_new_post(post):
    # pprint(post)
    all_categories = post.category.all()
    # print('Checkpoint 1')
    # pprint(all_categories)

    for a_category in all_categories:
        all_subscribers = a_category.subscribers.all()
        # print('Checkpoint 2')
        for a_subscriber in all_subscribers:
            email_list = []
            # print('Checkpoint 3')
            if is_email_valid(a_subscriber.email):
                email_list.append(a_subscriber.email)
                # Have to use to a single user at a time to address by name.
                # Not economical.
                # It would be faster and better to distribute a message to a whole list.
                # But how to address the users personally in this case?
                # print('Checkpoint 4')
                notify_about_new_post_subscribers(
                    post,
                    'post_created_notify.html',
                    a_category.name,
                    a_subscriber.username,
                    # salutation is needed to personalize email. Can be general 'friend'.
                    # Or it can be a user name. It this case, however, make sure there are only
                    # emails associated with this user in the email_list below.
                    email_list
                )


# End of file
