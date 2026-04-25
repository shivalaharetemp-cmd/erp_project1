from django.urls import path
from . import views

urlpatterns = [
    path('invoices/', views.sale_list, name='sale_list'),
    path('invoices/<uuid:pk>/', views.sale_detail, name='sale_detail'),
    path('credit-notes/', views.credit_note_list, name='credit_note_list'),
    path('credit-notes/create/', views.credit_note_create, name='credit_note_create'),
    path('credit-notes/<uuid:pk>/', views.credit_note_detail, name='credit_note_detail'),
]
