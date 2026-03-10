
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('add/', views.add_equipment, name='add_equipment'),
    # path('', views.map_view, name='map_view'), # We'll fill this in later
]