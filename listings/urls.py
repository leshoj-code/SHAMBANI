
from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('add/', views.add_equipment, name='add_equipment'),

    path('', views.home, name='index' ),

    path('starter/', views.starter, name='starter'),

    path('map/', views.map_view, name='map_view'),

    path('toggle/<int:pk>/', views.toggle_status, name='toggle_status'),

    path('pay/<int:pk>/', views.pay_for_machinery, name='pay_for_machinery'),

    path('request-order/<int:equipment_id>/', views.request_order, name='request_order'),

    path('signup/', views.signup_view, name='signup'),

    path('login/', views.login_view, name='login'), 
    
    path('logout/', views.logout_view, name='logout'),

    path('accept-order/', views.accept_order, name='accept_order'),

]