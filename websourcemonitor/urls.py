# coding=utf-8
from django.contrib import admin
from django.urls import path
from .views import diff, signal

admin.autodiscover()

urlpatterns = [
    path("diff/<int:content_id>/", diff, name='diff'),
    path("signal/<int:content_id>/", signal, name='signal'),
]
