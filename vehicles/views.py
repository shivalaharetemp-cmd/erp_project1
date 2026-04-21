from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Vehicle, VehicleItem, VehicleChangeLog
from .forms import VehicleCreateForm, VehicleUpdateForm, VehicleLoadForm, VehicleCancelForm, VehicleChangeForm
from .services import VehicleService


def _company_id(request):
    return request.session.get('company_id')


@login_required
def vehicle_list(request):
    cid = _company_id(request)
    
    # Get all companies for this user
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    # Show vehicles from all user's companies + company-neutral vehicles
    from django.db.models import Q
    qs = Vehicle.objects.filter(
        Q(company_id__in=user_company_ids) | Q(company__isnull=True)
    ).select_related('transporter', 'party', 'company', 'created_by').order_by('-created_at')
    
    status = request.GET.get('status', '')
    if status:
        qs = qs.filter(status=status)
    return render(request, 'vehicles/vehicle_list.html', {'vehicles': qs, 'status_filter': status})


@login_required
def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleCreateForm(request.POST)
        if form.is_valid():
            vehicle = VehicleService.create_vehicle(
                data=form.cleaned_data, user=request.user, request=request
            )
            messages.success(request, f'Vehicle {vehicle.vehicle_number} created.')
            return redirect('vehicle_detail', pk=vehicle.id)
    else:
        form = VehicleCreateForm()
    return render(request, 'vehicles/vehicle_form.html', {'form': form, 'title': 'Create Vehicle'})


@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    items = vehicle.items.select_related('item').all()
    freights = vehicle.freights.filter(is_active=True)
    has_invoice = hasattr(vehicle, 'sale') and vehicle.sale is not None
    sale = vehicle.sale if has_invoice else None
    change_logs = vehicle.change_logs.select_related('changed_by').all()

    # Check PO rates for loaded items (if company is assigned)
    po_rates = {}
    if vehicle.status == 'Loaded' and not has_invoice and vehicle.company:
        for vi in items:
            rate, po_num = VehicleService.get_po_rate(vehicle.party, vi.item, vehicle.company)
            po_rates[vi.id] = {'rate': rate, 'po_number': po_num}

    return render(request, 'vehicles/vehicle_detail.html', {
        'vehicle': vehicle, 'items': items, 'freights': freights,
        'has_invoice': has_invoice, 'sale': sale, 'change_logs': change_logs,
        'po_rates': po_rates,
    })


@login_required
def vehicle_edit(request, pk):
    from django.db.models import Q
    vehicle = get_object_or_404(Vehicle, pk=pk)
    cid = _company_id(request)
    # Check authorization: vehicle must be company-neutral or assigned to current company
    if vehicle.company_id is not None and vehicle.company_id != cid:
        return get_object_or_404(Vehicle, pk=None)  # Unauthorized access
    if not vehicle.is_editable:
        messages.error(request, f"Cannot edit vehicle with status: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    if request.method == 'POST':
        form = VehicleUpdateForm(request.POST, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vehicle updated.')
            return redirect('vehicle_detail', pk=pk)
    else:
        form = VehicleUpdateForm(instance=vehicle)
    return render(request, 'vehicles/vehicle_form.html', {'form': form, 'title': 'Edit Vehicle'})


@login_required
def vehicle_load(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if vehicle.status != 'Pending':
        messages.error(request, f"Cannot load vehicle with status: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    items_count = int(request.GET.get('items', 1))
    if request.method == 'POST':
        items_count = int(request.POST.get('items_count', items_count))
        form = VehicleLoadForm(request.POST, items_count=items_count)
        if form.is_valid():
            items_data = []
            for i in range(items_count):
                item_id = form.cleaned_data.get(f'item_{i}')
                quantity = form.cleaned_data.get(f'quantity_{i}')
                if item_id and quantity:
                    items_data.append({'item_id': str(item_id.id), 'quantity': quantity})
            if items_data:
                try:
                    vehicle = VehicleService.load_vehicle(vehicle, items_data, request.user, request)
                    messages.success(request, f'Vehicle {vehicle.vehicle_number} loaded.')
                    return redirect('vehicle_detail', pk=pk)
                except ValueError as e:
                    messages.error(request, str(e))
    else:
        form = VehicleLoadForm(items_count=items_count)

    # Build field pairs for template rendering
    field_pairs = []
    for i in range(items_count):
        field_pairs.append({
            'index': i,
            'item_field': form[f'item_{i}'],
            'qty_field': form[f'quantity_{i}'],
        })

    return render(request, 'vehicles/vehicle_load.html', {
        'vehicle': vehicle, 'form': form, 'items_count': items_count,
        'field_pairs': field_pairs,
    })


@login_required
def vehicle_cancel(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    cid = _company_id(request)
    # Check authorization: vehicle must be company-neutral or assigned to current company
    if vehicle.company_id is not None and vehicle.company_id != cid:
        return get_object_or_404(Vehicle, pk=None)  # Unauthorized access
    if vehicle.status == 'Cancelled':
        messages.error(request, 'Vehicle is already cancelled.')
        return redirect('vehicle_detail', pk=pk)

    if request.method == 'POST':
        form = VehicleCancelForm(request.POST)
        if form.is_valid():
            try:
                vehicle = VehicleService.cancel_vehicle(vehicle, form.cleaned_data['reason'], request.user, request)
                messages.success(request, f'Vehicle {vehicle.vehicle_number} cancelled.')
                return redirect('vehicle_detail', pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = VehicleCancelForm()
    return render(request, 'vehicles/vehicle_cancel.html', {'vehicle': vehicle, 'form': form})


@login_required
def vehicle_change(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    cid = _company_id(request)
    # Check authorization: vehicle must be company-neutral or assigned to current company
    if vehicle.company_id is not None and vehicle.company_id != cid:
        return get_object_or_404(Vehicle, pk=None)  # Unauthorized access

    if not request.user.has_role_permission(['admin', 'manager']):
        messages.error(request, "You don't have permission to change vehicle number.")
        return redirect('vehicle_detail', pk=pk)

    if vehicle.status not in ('Pending', 'Loaded'):
        messages.error(request, f"Cannot change vehicle number for status: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    if request.method == 'POST':
        form = VehicleChangeForm(request.POST)
        if form.is_valid():
            try:
                vehicle = VehicleService.change_vehicle(
                    vehicle, form.cleaned_data['new_vehicle_number'],
                    form.cleaned_data['reason'], request.user, request
                )
                messages.success(request, f'Vehicle number changed to {vehicle.vehicle_number}.')
                return redirect('vehicle_detail', pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = VehicleChangeForm()
    return render(request, 'vehicles/vehicle_change.html', {'vehicle': vehicle, 'form': form})


@login_required
def vehicle_create_sale(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if vehicle.status != 'Loaded':
        messages.error(request, f"Vehicle must be Loaded to create sale. Current: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    if hasattr(vehicle, 'sale') and vehicle.sale:
        messages.error(request, 'Sale already exists for this vehicle.')
        return redirect('vehicle_detail', pk=pk)

    from sales.forms import SaleCreateForm
    from sales.services import SaleService
    from vehicles.services import VehicleService
    from core.models import Company
    
    vehicle_items = vehicle.items.select_related('item').all()
    companies = Company.objects.filter(is_active=True)

    if request.method == 'POST':
        form = SaleCreateForm(request.POST, vehicle_items=vehicle_items, companies=companies)
        if form.is_valid():
            selected_company = form.cleaned_data.get('company')

            # Build items data
            items_data = []
            for i, vi in enumerate(vehicle_items):
                rate = form.cleaned_data.get(f'rate_{i}')
                if rate:
                    items_data.append({'vehicle_item_id': str(vi.id), 'rate': float(rate)})
            
            try:
                # Update session company to selected company
                request.session['company_id'] = str(selected_company.id)
                
                # Set the company on vehicle before creating sale
                vehicle.company = selected_company
                vehicle.save(update_fields=['company'])
                
                sale = SaleService.create_sale(vehicle, items_data, request.user, request)
                messages.success(request, f'Invoice {sale.invoice_number} generated for {selected_company.name}.')
                return redirect('sale_detail', pk=sale.id)
            except ValueError as e:
                messages.error(request, str(e))
        
        # If form is invalid, prepare po_options_all for re-render
        po_options_all = {}
        for company in companies:
            po_options_all[str(company.id)] = {}
            for vi in vehicle_items:
                options = VehicleService.get_all_po_options(vehicle.party, vi.item, company)
                po_options_all[str(company.id)][str(vi.id)] = options
        
        # Convert Decimal values to float and dates to strings for JSON serialization
        import json
        po_options_json = json.dumps({
            cid: {
                vid: [
                    {**po, 'rate': float(po['rate']), 'po_date': str(po['po_date'])} for po in pos
                ] for vid, pos in items.items()
            } for cid, items in po_options_all.items()
        })
    else:
        form = SaleCreateForm(vehicle_items=vehicle_items, companies=companies)
        # Pre-fetch PO options for ALL companies
        po_options_all = {}
        for company in companies:
            po_options_all[str(company.id)] = {}
            for vi in vehicle_items:
                options = VehicleService.get_all_po_options(vehicle.party, vi.item, company)
                po_options_all[str(company.id)][str(vi.id)] = options

    # Convert Decimal values to float and dates to strings for JSON serialization
    import json
    po_options_json = json.dumps({
        cid: {
            vid: [
                {**po, 'rate': float(po['rate']), 'po_date': str(po['po_date'])} for po in pos
            ] for vid, pos in items.items()
        } for cid, items in po_options_all.items()
    })

    return render(request, 'vehicles/vehicle_create_sale.html', {
        'vehicle': vehicle, 'form': form, 'vehicle_items': vehicle_items, 'po_options_json': po_options_json
    })
