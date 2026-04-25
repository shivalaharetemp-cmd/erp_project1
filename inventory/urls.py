from django.urls import path
from . import views

urlpatterns = [
    path('stock/', views.stock_list, name='stock_list'),
    path('stock/<uuid:pk>/', views.stock_detail, name='stock_detail'),
    path('movements/', views.stock_movement_list, name='stock_movement_list'),
    path('adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),
]
