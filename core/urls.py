from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import forms

urlpatterns = [
    path('', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=forms.ERPLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('company/select/', views.select_company, name='company_select'),
    path('company/select/<uuid:company_id>/', views.do_select_company, name='select_company'),
    path('change-password/', views.change_password, name='change_password'),
]
