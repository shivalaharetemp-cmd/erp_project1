from django.urls import path
from . import views

urlpatterns = [
    path('parties/', views.party_list, name='party_list'),
    path('parties/create/', views.party_create, name='party_create'),
    path('parties/<uuid:pk>/', views.party_detail, name='party_detail'),
    path('parties/<uuid:pk>/edit/', views.party_edit, name='party_edit'),

    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<uuid:pk>/', views.item_detail, name='item_detail'),
    path('items/<uuid:pk>/edit/', views.item_edit, name='item_edit'),

    path('transporters/', views.transporter_list, name='transporter_list'),
    path('transporters/create/', views.transporter_create, name='transporter_create'),
    path('transporters/<uuid:pk>/', views.transporter_detail, name='transporter_detail'),
    path('transporters/<uuid:pk>/edit/', views.transporter_edit, name='transporter_edit'),

    path('purchase-orders/', views.po_list, name='po_list'),
    path('purchase-orders/create/', views.po_create, name='po_create'),
    path('purchase-orders/<uuid:pk>/', views.po_detail, name='po_detail'),
    path('purchase-orders/<uuid:pk>/edit/', views.po_edit, name='po_edit'),
]
