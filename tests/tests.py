import os
import datetime
import mailing
import names

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from registration.models import Subject, Event

mailing.DEADTIME = 0


class SubjectTestCase(TestCase):
    def setUp(self):
        self.ev = Event.objects.create(
            title='Test',
            num_total_seats=20,
            enable_on=timezone.now() - datetime.timedelta(days=1),
            disable_on=timezone.now() + datetime.timedelta(days=1),
        )

    def create_subject(self):
        name = names.get_full_name().split()
        email = '%s@test.com' % '.'.join(map(str.lower, name))
        return Subject.objects.create(
            name=name[0],
            given_name=name[1],
            email=email,
            event=self.ev,
        )

    def test_mailing(self):
        for i in range(20):
            subj = self.create_subject()
            mailing.confirmation_request_mail(subj)
            # print(mail.outbox[-1].subject, mail.outbox[-1].message())
            # mailing.remainder_mail(subj)
            # print(mail.outbox[-1].subject, mail.outbox[-1].message())
            # mailing.confirmation_mail(subj)
            # print(mail.outbox[-1].subject, mail.outbox[-1].message())
            # mailing.cancellation_mail(subj)
            # print(mail.outbox[-1].subject, mail.outbox[-1].message())
            # break
        print(Subject.objects.count())

    def test_index_page_url(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='registration/subject_form_create.html')

    def test_index_page_view_name(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='registration/subject_form_create.html')

    def test_index_page_create_subject(self):
        for i in range(50):
            name = names.get_full_name().split()
            email = '%s@test.com' % '.'.join(map(str.lower, name))
            response = self.client.post(reverse('index'),
                data=dict(
                    name=name[0],
                    given_name=name[1],
                    email=email,
                    event=self.ev.pk,
                    num_seats=(i % 5)+1,
                )
            )

            # form validation error
            if response.status_code == 200:
                break

            # redirected to next page
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/submitted'))

            if i % 2:
                Subject.objects.filter(email=email).delete()
        print(self.ev.seats_taken)

    def test_create(self):
        self.assertEqual(self.ev.seats_taken, 0)
        self.create_subject()
        self.assertEqual(self.ev.seats_taken, 1)

    def test_confirm(self):
        subj = self.create_subject()
        self.assertFalse(subj.status_confirmed)
        response = self.client.get(reverse('subject-confirm', kwargs={'token': subj.token}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='registration/confirm.html')
        self.assertTrue(Subject.objects.filter(pk=subj.pk).first().status_confirmed)

    def test_modify(self):
        subj = self.create_subject()
        response = self.client.get(reverse('subject-modify', kwargs={'slug': subj.token}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='registration/subject_form.html')
        data = response.context['form'].fields
        data['num_seats'] = 2
        response = self.client.post(
            reverse('subject-modify', kwargs={'slug': subj.token}), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(os.path.join('/', subj.token, 'modify')))
        self.assertEqual(self.ev.seats_taken, 2)

    def test_delete(self):
        subj = self.create_subject()
        response = self.client.get(reverse('subject-delete', kwargs={'slug': subj.token}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='registration/subject_confirm_delete.html')
        response = self.client.post(reverse('subject-delete', kwargs={'slug': subj.token}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/'))
        self.assertEqual(Subject.objects.filter(pk=subj.pk).count(), 0)
        self.assertEqual(self.ev.seats_taken, 0)
