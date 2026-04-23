from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Company, User, CompanyUser
from .forms import ERPLoginForm, ChangePasswordForm
from audit.services import AuditService


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    company_id = request.session.get('company_id')
    if not company_id:
        return redirect('company_select')

    from vehicles.models import Vehicle
    from sales.models import Sale

    # Get all companies for this user
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)

    ctx = {
        # Vehicles are neutral - count all, not by company
        'pending_vehicles': Vehicle.objects.filter(status='Pending').count(),
        'loaded_vehicles': Vehicle.objects.filter(status='Loaded').count(),
        'cancelled_vehicles': Vehicle.objects.filter(status='Cancelled').count(),
        # Sales are company-linked
        'active_invoices': Sale.objects.filter(company_id__in=user_company_ids, status='Active').count(),
        # Recent vehicles - all vehicles are neutral (no is_active field on Vehicle)
        'recent_vehicles': Vehicle.objects.all().select_related(
            'transporter', 'party'
        ).order_by('-created_at')[:10],
    }
    return render(request, 'core/dashboard.html', ctx)


@login_required
def select_company(request):
    companies = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).select_related('company')
    if companies.count() == 1:
        cu = companies.first()
        request.session['company_id'] = str(cu.company.id)
        request.session['company_name'] = cu.company.name
        return redirect('dashboard')
    return render(request, 'core/company_select.html', {'companies': companies})


@login_required
def do_select_company(request, company_id):
    try:
        cu = CompanyUser.objects.get(user=request.user, company_id=company_id, is_active=True)
    except CompanyUser.DoesNotExist:
        messages.error(request, "You don't have access to this company.")
        return redirect('company_select')

    request.session['company_id'] = str(cu.company.id)
    request.session['company_name'] = cu.company.name

    AuditService.log(
        user=request.user, company=cu.company, action='SELECT_COMPANY',
        model_name='Company', object_id=str(company_id), request=request,
    )
    messages.success(request, f"Switched to {cu.company.name}")
    return redirect('dashboard')


@login_required
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            old = form.cleaned_data['old_password']
            new = form.cleaned_data['new_password']
            if not request.user.check_password(old):
                form.add_error('old_password', 'Old password is incorrect.')
            else:
                request.user.set_password(new)
                request.user.save()
                messages.success(request, 'Password changed successfully.')
                return redirect('dashboard')
    else:
        form = ChangePasswordForm()
    return render(request, 'core/change_password.html', {'form': form})
