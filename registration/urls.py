from django.shortcuts import render
from django.urls import path

from . import views

urlpatterns = [
    path('', views.CreateSubjectView.as_view(), name='index'),
    path('privacy', lambda r: render(r, "registration/privacy.html"), name='privacy'),
    path('site_notice', lambda r: render(r, "registration/site_notice.html"), name='site_notice'),
    path('<token>/confirm', views.confirm, name='subject-confirm'),
    path('<slug:slug>/modify', views.SubjectView.as_view(), name='subject-modify'),
    path('<slug:slug>/delete', views.DeleteSubjectView.as_view(), name='subject-delete'),
    path('submitted', views.submitted, name='submitted'),
    path('subjects', views.ListSubjectView.as_view(), name='subjects'),
    path('subjects/create', views.CreateSubjectViewAdmin.as_view(), name='subjects-create'),
    path('subjects/<slug:pk>', views.SubjectViewAdmin.as_view(), name='subjects-detail'),
    path('events', views.ListEventView.as_view(), name='events'),
    path('events/create', views.CreateEventView.as_view(), name='events-create'),
    path('events/<slug:pk>/delete', views.DeleteEventView.as_view(), name='events-delete'),
    path('events/<slug:pk>/participants', views.subject_table, name='events-participants'),
    path('events/<slug:pk>', views.EventView.as_view(), name='events-detail'),
]