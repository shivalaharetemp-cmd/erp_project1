from django.urls import path
from . import views

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('create/', views.vehicle_create, name='vehicle_create'),
    path('<uuid:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('<uuid:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('<uuid:pk>/load/', views.vehicle_load, name='vehicle_load'),
    path('<uuid:pk>/cancel/', views.vehicle_cancel, name='vehicle_cancel'),
    path('<uuid:pk>/change-vehicle/', views.vehicle_change, name='vehicle_change'),
    path('<uuid:pk>/create-sale/', views.vehicle_create_sale, name='vehicle_create_sale'),
    path('<uuid:pk>/dispatch/', views.vehicle_dispatch, name='vehicle_dispatch'),
    path('<uuid:pk>/deliver/', views.vehicle_deliver, name='vehicle_deliver'),
]
