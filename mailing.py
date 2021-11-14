import os
import time
import django

from datetime import timedelta

from django.utils import timezone
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _, ngettext, ngettext_lazy
from django.db.models import Q

os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()

# needs to be after django.setup()
from registration.models import Subject
from mysite.settings import DEFAULT_FROM_EMAIL, BASE_URL

# intervall for checking for new mails to be send
INTERVAL = 30
# deadtime after a mail has been sent (mail server has 10 Mails/minute restriction)
DEADTIME = 10
confirm_url = lambda base, token: os.path.join(base, token, 'confirm')
modify_url = lambda base, token: os.path.join(base, token, 'modify')

def do_send_mail(subject, message, to):
    try:
        send_mail(subject, message, DEFAULT_FROM_EMAIL, [to])
        time.sleep(DEADTIME)
        return True        
    except Exception as e:
        print(e)
        return False    

## send when the subject registers for the event,
## contains the link for the registration confirmation
def confirmation_request_mail(sub):
    subject = _('Registration for %s')
    message = _('mail_body_%(name)s_%(event)s_%(hold_back_hours)i_%(confirm_url)s')

    subject = subject%sub.event.title
    message = message%dict(
        name=sub.given_name,
        event=sub.event,
        hold_back_hours=sub.event.hold_back_hours,
        confirm_url=confirm_url(BASE_URL, sub.token),
        modify_url=modify_url(BASE_URL, sub.token)
    )
    return do_send_mail(subject, message, sub.email)

## send after some timeout to warn about registration deletion
def remainder_mail(sub):
    subject = _('Reminder of registration for %s')
    message = _('reminder_body_%(name)s_%(event)s_%(cancel_hours)i_%(confirm_url)s_%(modify_url)s')

    subject = subject%sub.event.title
    message = message%dict(
        name=sub.given_name,
        event=sub.event,
        cancel_hours=sub.event.hold_back_hours - sub.event.reminder_hours,
        confirm_url=confirm_url(BASE_URL, sub.token),
        modify_url=modify_url(BASE_URL, sub.token)
    )
    return do_send_mail(subject, message, sub.email)

## send when the subject clicked on the registration confirmation link
def confirmation_mail(sub):
    subject = _('Confirmed registration for %s')
    message = _('confirmation_body_%(name)s_%(event)s_%(modify_url)s_%(seats)s')

    seats = ''
    if sub.event.assigned_seats:
        seats = _(ngettext_lazy(
            'subject_seats_%(seat_nums)s',
            'subject_seats_pl_%(seat_nums)s',
            sub.num_seats))%dict(seat_nums=sub.seats)
        seats += '\n(Plan: %s/static/registration/GHS_physik.pdf)\n'%BASE_URL

    subject = subject%sub.event.title
    message = message%dict(
        name=sub.given_name,
        event=sub.event,
        seats=seats,
        modify_url=modify_url(BASE_URL, sub.token),
    )
    return do_send_mail(subject, message, sub.email)

def cancellation_mail(sub):
    subject = _('Cancellation of registration for %s')
    message = _('cancellation_body_%(name)s_%(event)s')

    subject = subject%sub.event.title
    message = message%dict(
        name=sub.given_name,
        event=sub.event,
    )    
    return do_send_mail(subject, message, sub.email)

def next_subject(query):
    try:
        sub = Subject.objects \
            .filter(query) \
            .order_by('reg_date')[0]
        return sub
    except:
        return None

def handle_new_subjects():
    while True:
        sub = next_subject(Q(confirmation_request_sent=False))
        if sub is None: return True
        if not confirmation_request_mail(sub): break
        sub.confirmation_request_sent = True
        sub.save()        
    return False

def handle_confirmed_subjects():
    while True:
        sub = next_subject(Q(status_confirmed=True) & Q(confirmation_sent=False))
        if sub is None: return True
        if not confirmation_mail(sub): break
        sub.confirmation_sent = True
        sub.save()        
    return False

def handle_pending_subjects():
    while True:
        # fetch new list of pending subjects
        subs = Subject.objects \
            .filter(confirmation_request_sent=True, status_confirmed=False) \
            .order_by('reg_date')

        # nothing to do anymore, so return
        if len(subs) == 0: return True

        # iterate over possible subject until one is found where email has to be send. Then
        # start all over to minimize risk that s.t. has changed in the DB in the meantime
        mail_sent=False
        for sub in subs:
            if not sub.reminder_sent:
                # check, how long ago the request was send... send remainder (once) if certain timeout hit
                if timezone.now() > sub.reg_date + timedelta(hours=sub.event.reminder_hours):
                    if not remainder_mail(sub): return False
                    sub.reminder_sent = True
                    sub.save()                    
                    mail_sent=True
                    break
            else:
                if timezone.now() > sub.reg_date + timedelta(hours=sub.event.hold_back_hours): 
                    if not cancellation_mail(sub): return False
                    sub.delete()
                    mail_sent=True
                    break

        # nothing to do for matching subjects
        if not mail_sent:
            return True

def mailer():
    if not handle_new_subjects(): return
    if not handle_pending_subjects(): return
    if not handle_confirmed_subjects(): return

if __name__ == "__main__":
    try:
        while True:
            mailer()
            time.sleep(INTERVAL)
    except (KeyboardInterrupt, SystemExit):
        print("Exiting")
    except Exception as e:
        raise e