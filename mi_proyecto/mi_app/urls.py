from django.urls import path
from . import views
from .views import calendar_events, new_meet


urlpatterns = [
    path('', calendar_events, name='calendar_events'),
    path('new_event/', new_meet, name='new_meet'),

]

