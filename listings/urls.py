
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('add/', views.add_equipment, name='add_equipment'),

    path('', views.home, name='home' ),

    path('starter/', views.starter, name='starter'),

    path('map/', views.map_view, name='map_view'),

    path('toggle/<int:pk>/', views.toggle_status, name='toggle_status'),

]