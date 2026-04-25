from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserCompaniesView.as_view(), name='user-companies'),
    path('select/', views.SelectCompanyView.as_view(), name='select-company'),
    path('context/', views.CompanyContextView.as_view(), name='company-context'),
    path('list/', views.CompanyListView.as_view(), name='company-list'),
]
