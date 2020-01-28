import os
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.core.mail import send_mail
from django.forms import models, ChoiceField
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext_lazy

from registration.models import Subject, Event
from registration.sub_table_tex import create_table

from mysite.settings import DEFAULT_FROM_EMAIL


def active_events():
    return Event.objects.filter(
        is_active=True, enable_on__lte=timezone.now(), disable_on__gte=timezone.now())


class EventsAvailableMixin:
    def dispatch(self, request, *args, **kwargs):
        events = active_events()
        if events.count()==0:
            return render(request, 'registration/no_events.html')

        if sum([ev.seats_taken<ev.num_total_seats for ev in events]) == 0:
            return render(request, 'registration/no_seats.html')

        return super().dispatch(request, *args, **kwargs)


class CustomModelChoiceIterator(models.ModelChoiceIterator):
    def choice(self, obj):
        return (self.field.prepare_value(obj),
                '%s%s'%(self.field.label_from_instance(obj),
                        '' if obj.seats_taken<obj.num_total_seats else ' - '+str(_('booked_out'))))


class CustomModelChoiceField(models.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return CustomModelChoiceIterator(self)
    choices = property(_get_choices,
                       ChoiceField._set_choices)


class SubjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        # do not allow to modify the email and event for a registration
        if self.instance and instance.pk:
            self.fields['event'].disabled = True
            self.fields['email'].disabled = True

    def clean_num_seats(self):
        instance = getattr(self, 'instance', None)
        if self.instance and instance.pk:
            ev = self.instance.event
        else:
            if not self.data['event']:
                return self.cleaned_data['num_seats']
            ev = self.cleaned_data['event']

        if self.cleaned_data['num_seats'] > ev.num_max_per_subject:
            raise ValidationError(ngettext_lazy(
                'max_seats_subj_exceeded_%(num_max)i',
                'max_seats_subj_exceeded_pl_%(num_max)i',
                ev.num_max_per_subject),
                code='invalid',
                params={'num_max': ev.num_max_per_subject})

        if self.instance and instance.pk:
            # seats taken includes only seats of confirmed registrations
            taken = ev.seats_taken
            if not instance.status_confirmed:
                taken += instance.num_seats

            # allow subject to decrease registration even if all seats are taken
            if taken >= ev.num_total_seats:
                if self.cleaned_data['num_seats'] > instance.num_seats:
                    raise ValidationError(_('no_seats_event'), code='invalid')
            # if not all seats are taken, allow subject to fill up seats up to num_total_seats
            elif taken-instance.num_seats+self.cleaned_data['num_seats'] > ev.num_total_seats:
                raise ValidationError(ngettext_lazy(
                    'max_seats_exceeded_%(num_free)i',
                    'max_seats_exceeded_pl_%(num_free)i',
                    ev.num_total_seats-taken), code='invalid', params={'num_free': ev.num_total_seats-taken})

        else:
            taken = ev.seats_taken
            # it is not possible to create a registration when there are no more seats available
            if taken >= ev.num_total_seats:
                raise ValidationError(_('no_seats_event'), code='invalid')

            # it is not possible to exceed the number of available seats
            if taken+self.cleaned_data['num_seats'] > ev.num_total_seats:
                raise ValidationError(ngettext_lazy(
                    'max_seats_exceeded_%(num_free)i',
                    'max_seats_exceeded_pl_%(num_free)i',
                    ev.num_total_seats-taken), code='invalid', params={'num_free': ev.num_total_seats-taken})

        return self.cleaned_data['num_seats']

    class Meta:
        model = Subject
        fields = ['name', 'given_name', 'email', 'event', 'num_seats']
        error_messages = {
            NON_FIELD_ERRORS: {
                'unique_together': "Es existiert bereits eine Registrierung für diese %(field_labels)s.",
            }
        }


class CreateSubjectView(EventsAvailableMixin, generic.CreateView):
    form_class = SubjectForm
    template_name = 'registration/subject_form_create.html'

    subject = _('Registration for %s')
    message = _('mail_body_%(name)s_%(event)s_%(confirm_url)s_%(modify_url)s')
    from_email = DEFAULT_FROM_EMAIL
    confirm_url = '%s%s/confirm'
    modify_url = '%s%s/modify'

    success_url = reverse_lazy('submitted')

    def get_context_data(self, **kwargs):
        context = super(CreateSubjectView, self).get_context_data(**kwargs)
        context['form'].fields['event'] = CustomModelChoiceField(
            widget = forms.Select,
            queryset = active_events()
        )
        return context

    def form_valid(self, form):
        # save the form
        redirect = super().form_valid(form)

        # create confirmation mail
        confirm_url = CreateSubjectView.confirm_url%(self.request.build_absolute_uri(), self.object.token)
        modify_url = CreateSubjectView.modify_url%(self.request.build_absolute_uri(), self.object.token)
        subject = CreateSubjectView.subject%self.object.event.title
        message = CreateSubjectView.message%dict(
            name=self.object.given_name,
            event=self.object.event,
            confirm_url=confirm_url,
            modify_url=modify_url
        )

        # send it
        try:
            send_mail(subject, message, CreateSubjectView.from_email, [self.object.email])
        except Exception as e:
            print(e)
            # if sending failed, delete the record
            self.object.delete()
            return HttpResponse(_('Cannot send mail.'))
        return redirect


class SubjectView(generic.UpdateView):
    model = Subject
    slug_field = 'token'
    form_class = SubjectForm
    template_name = 'registration/subject_form.html'


class SubjectViewAdmin(LoginRequiredMixin, generic.UpdateView):
    model = Subject
    fields = ['name', 'given_name', 'email', 'event', 'num_seats', 'status_confirmed']
    success_url = reverse_lazy('subjects')


class CreateSubjectViewAdmin(LoginRequiredMixin, generic.CreateView):
    model = Subject
    fields = ['name', 'given_name', 'email', 'event', 'num_seats', 'status_confirmed']
    template_name = 'registration/subject_form_create.html'
    success_url = reverse_lazy('subjects')


def submitted(request):
    return render(request, 'registration/submitted.html')


def confirm(request, token):
    sub = get_object_or_404(Subject.objects.filter(token=token))
    subject = _('Confirmed registration for %s')
    message = _('confirmation_body_%(name)s_%(event)s_%(modify_url)s')
    if not sub.status_confirmed:
        try:
            send_mail(
                subject,
                message%dict(
                    name=sub.given_name,
                    event=sub.event,
                    modify_url=request.build_absolute_uri(reverse('subject-modify', args=[sub.token]))
                ),
                CreateSubjectView.from_email,
                [sub.email])
            sub.status_confirmed = True
            sub.confirmation_sent = True
            sub.save()
        except Exception as e:
            print(e)
            return HttpResponse(_('Cannot send mail.'))
    return render(request, 'registration/confirm.html', {'subject': sub, 'event': sub.event})


class DeleteSubjectView(generic.DeleteView):
    model = Subject
    slug_field = 'token'
    success_url = reverse_lazy('index')


class FilterForm(forms.Form):
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        empty_label="(Nothing)",
        widget=forms.Select(attrs={"onChange":'filter(this)'}))


class ListSubjectView(LoginRequiredMixin, generic.ListView):
    model = Subject

    def get_queryset(self):
        filter_val = self.request.GET.get('event', None)
        if filter_val is None:
            return super(ListSubjectView, self).get_queryset()

        queryset = Subject.objects.filter(event=filter_val)

        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, str):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ListSubjectView, self).get_context_data(**kwargs)
        context['filter'] = FilterForm()
        filter_val = self.request.GET.get('event', None)
        if filter_val is not None:
            context['filter'].fields['event'].initial = Event.objects.filter(id=filter_val).first()
        return context


class ListEventView(LoginRequiredMixin, generic.ListView):
    model = Event


class EventViewBase(LoginRequiredMixin):
    model = Event
    success_url = reverse_lazy('events')


class CreateEventView(EventViewBase, generic.CreateView):
    fields = ['title', 'date', 'is_active', 'enable_on', 'disable_on', 'num_total_seats', 'num_max_per_subject']
    template_name = 'registration/event_form_create.html'

    def get_context_data(self, **kwargs):
        context = super(CreateEventView, self).get_context_data(**kwargs)
        # context['form'].fields['date'].input_formats = ['%d.%m.%y %H:%M']
        return context


class EventForm(forms.ModelForm):
    seats_taken = forms.CharField(disabled=True, required=False)

    class Meta:
        model = Event
        fields = ['title', 'date', 'is_active', 'enable_on', 'disable_on', 'num_total_seats', 'num_max_per_subject', 'seats_taken']


class EventView(EventViewBase, generic.UpdateView):
    form_class = EventForm
    template_name = 'registration/event_form.html'
    success_url = reverse_lazy('events')

    def get_context_data(self, **kwargs):
        context = super(EventView, self).get_context_data(**kwargs)
        context['form'].fields['seats_taken'].initial = self.object.seats_taken
        # context['form'].fields['date'].input_formats = ['%d.%m.%y %H:%M']
        return context


class DeleteEventView(EventViewBase, generic.DeleteView):
    pass


def subject_table(request, pk):
    event = get_object_or_404(Event.objects.filter(pk=pk))
    subs = Subject.objects.filter(event=event).order_by('name', 'given_name', 'email')
    file_path = create_table(subs)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/pdf")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404


