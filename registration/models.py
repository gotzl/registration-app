import secrets

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class Event(models.Model):
    title = models.CharField(max_length=1024, help_text='name of the event')
    date = models.DateTimeField(default=timezone.now, help_text='date and time of the event')
    is_active = models.BooleanField(default=True)
    num_total_seats = models.IntegerField(help_text="total number of seats available")
    num_max_per_subject = models.IntegerField(default=5, help_text="maximum number of seats that can be booked by one person")
    enable_on = models.DateTimeField(_('enable_on'), default=timezone.now)
    disable_on = models.DateTimeField(_('disable_on'), default=timezone.now)

    @property
    def seats_taken(self):
        return sum(map(lambda x: x.num_seats, Subject.objects.filter(event=self, status_confirmed=True)))

    def get_absolute_url(self):
        return reverse('event-detail', args=[self.id])

    def __str__(self):
        return _("'%(title)s' on %(date)s")%dict(title=self.title, date=timezone.localtime(self.date).strftime('%d.%m.%y %H:%M'))


def token():
    return secrets.token_urlsafe(32)


class Subject(models.Model):
    name = models.CharField(_('name'), max_length=200)
    given_name = models.CharField(_('given_name'), max_length=200)
    email = models.EmailField(_('email'), max_length=200)

    event = models.ForeignKey(Event, verbose_name=_('event'), on_delete=models.CASCADE)
    reg_date = models.DateTimeField(_('reg_date'), default=timezone.now)
    num_seats = models.IntegerField(_('num_seats'), default=1, validators=[MinValueValidator(1)])

    status_confirmed = models.BooleanField(_('status_confirmed'), default=False)
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    token = models.CharField(max_length=32, default=token)

    class Meta:
        unique_together = ('event', 'email')

    def get_absolute_url(self):
        return reverse('subject-modify', args=[self.token])

    def __str__(self):
        return "%s"%(self.event)
