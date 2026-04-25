from django.urls import path
from . import views

urlpatterns = [
    path('receivables/', views.receivable_list, name='receivable_list'),
    path('receivables/<uuid:pk>/', views.receivable_detail, name='receivable_detail'),
    path('receivables/<uuid:pk>/add-receipt/', views.add_receipt, name='add_receipt'),
    path('payables/', views.payable_list, name='payable_list'),
    path('payables/<uuid:pk>/', views.payable_detail, name='payable_detail'),
    path('payables/<uuid:pk>/add-payment/', views.add_payment, name='add_payment'),
    path('ledger/', views.ledger_list, name='ledger_list'),
    path('transporter-bills/', views.transporter_bill_list, name='transporter_bill_list'),
]
