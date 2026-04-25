from django.urls import path
from . import views

urlpatterns = [
    path('', views.freight_list, name='freight_list'),
    path('create/', views.freight_create, name='freight_create'),
    path('<uuid:pk>/update/', views.freight_update, name='freight_update'),
    path('vehicle/<uuid:vehicle_id>/', views.freight_by_vehicle, name='freight_by_vehicle'),
    path('return/create/', views.return_freight_create, name='return_freight_create'),
    path('<uuid:pk>/deactivate/', views.freight_deactivate, name='freight_deactivate'),
]
