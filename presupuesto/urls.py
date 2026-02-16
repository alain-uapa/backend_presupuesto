from django.contrib import admin
from django.urls import path
from presupuesto.solicitudes_view import solicitudes_list

urlpatterns = [
    path("solicitudes/list", solicitudes_list, name='solicitudes_list'),    
]