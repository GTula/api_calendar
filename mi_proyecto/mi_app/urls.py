from django.urls import path
from . import views
from .views import calendar_events


urlpatterns = [
    path('', calendar_events, name='calendar_events'),
]

