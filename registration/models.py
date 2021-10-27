import secrets

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.core.validators import int_list_validator

from mysite import settings


class Event(models.Model):
    title = models.CharField(max_length=1024, help_text='name of the event')
    date = models.DateTimeField(default=timezone.now, help_text='date and time of the event')
    is_active = models.BooleanField(default=True)
    num_total_seats = models.IntegerField(help_text="total number of seats available")
    num_max_per_subject = models.IntegerField(default=5, help_text="maximum number of seats that can be booked by one person")
    enable_on = models.DateTimeField(_('enable_on'), default=timezone.now)
    disable_on = models.DateTimeField(_('disable_on'), default=timezone.now)
    assigned_seats = models.BooleanField(default=False, help_text="each entry has an assigned seat number")
    reminder_hours = models.IntegerField(default=12, help_text="hours to wait after registration before sending the reminder for the registration confirmation")
    hold_back_hours = models.IntegerField(default=24, help_text="hours to wait after registration before cancelling a registration that was not confirmed")

    @property
    def seats_taken(self):
        return sum(map(lambda x: x.num_seats, Subject.objects.filter(event=self)))

    def get_absolute_url(self):
        return reverse('event-detail', args=[self.id])

    def __str__(self):
        return _("'%(title)s' on %(date)s")%dict(title=self.title, date=timezone.localtime(self.date).strftime('%d.%m.%y %H:%M'))


def token():
    return secrets.token_urlsafe(32)


class SubjectBase(models.Model):
    name = models.CharField(_('name'), max_length=200)
    given_name = models.CharField(_('given_name'), max_length=200)
    email = models.EmailField(_('email'), max_length=200)

    event = models.ForeignKey(Event, verbose_name=_('event'), on_delete=models.CASCADE)
    reg_date = models.DateTimeField(_('reg_date'), default=timezone.now)
    num_seats = models.IntegerField(_('num_seats'), default=1, validators=[MinValueValidator(1)])
    seats = models.CharField(_('seats'), max_length=1024, default='', validators=[int_list_validator])

    status_confirmed = models.BooleanField(_('status_confirmed'), default=False)
    confirmation_request_sent = models.BooleanField(_('confirmation_request_sent'), default=False)
    confirmation_sent = models.BooleanField(_('confirmation_sent'), default=False)
    reminder_sent = models.BooleanField(_('reminder_sent'), default=False)
    token = models.CharField(max_length=255, default=token)

    class Meta:
        unique_together = ('event', 'email')

    def get_absolute_url(self):
        return reverse('subject-modify', args=[self.token])

    def __str__(self):
        return "%s"%(self.event)


class SubjectExtended(SubjectBase):
    address = models.CharField(_('address'), max_length=50)
    city = models.CharField(_('city'), max_length=60)
    post_code = models.IntegerField(_('post_code'))
    phone = models.CharField(_('phone'), max_length=50)


Subject = eval(settings.SUBJECT_CLASS)
