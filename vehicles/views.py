from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Vehicle, VehicleItem, VehicleChangeLog
from .forms import VehicleCreateForm, VehicleUpdateForm, VehicleLoadForm, VehicleCancelForm, VehicleChangeForm, VehicleDispatchForm, VehicleDeliveryForm
from .services import VehicleService


def _company_id(request):
    return request.session.get('company_id')


@login_required
def vehicle_list(request):
    cid = _company_id(request)
    
    # Get all companies for this user
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user
    ).values_list('company_id', flat=True)
    
    # Show vehicles from all user's companies + company-neutral vehicles
    from django.db.models import Q
    qs = Vehicle.objects.filter(
        Q(company_id__in=user_company_ids) | Q(company__isnull=True)
    ).select_related('transporter', 'party', 'company', 'created_by').prefetch_related('freights').order_by('-created_at')
    
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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
    items = vehicle.items.select_related('item').all()
    freights = vehicle.freights.filter(is_active=True)
    # Get the most recent active sale for this vehicle (supports multiple sales per vehicle)
    sale = vehicle.sales.filter(status='Active').order_by('-created_at').first()
    has_invoice = sale is not None
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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)

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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
    if vehicle.status != 'Loaded':
        messages.error(request, f"Vehicle must be Loaded to create sale. Current: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    # Allow multiple sales per vehicle - just show info message
    existing_sales_count = vehicle.sales.filter(status='Active').count()
    if existing_sales_count > 0:
        messages.info(request, f'Note: This vehicle already has {existing_sales_count} active sale(s). You can create another one.')

    from sales.forms import SaleCreateForm
    from sales.services import SaleService
    from vehicles.services import VehicleService
    from core.models import Company
    from masters.models import LoadingPoint

    vehicle_items = vehicle.items.select_related('item').all()
    companies = Company.objects.filter(is_active=True)
    loading_points = LoadingPoint.objects.filter(is_active=True)

    if request.method == 'POST':
        form = SaleCreateForm(request.POST, vehicle_items=vehicle_items, companies=companies, loading_points=loading_points)
        if form.is_valid():
            selected_company = form.cleaned_data.get('company')

            # Build items data from selected checkboxes
            items_data = []
            for i, vi in enumerate(vehicle_items):
                include = form.cleaned_data.get(f'include_{i}')
                if include:
                    qty = form.cleaned_data.get(f'qty_{i}')
                    rate = form.cleaned_data.get(f'rate_{i}')
                    if qty and rate:
                        # Validate quantity doesn't exceed remaining
                        if qty > vi.remaining_quantity:
                            messages.error(request, f'Quantity for {vi.item.item_name} exceeds remaining ({vi.remaining_quantity})')
                            break
                        items_data.append({
                            'vehicle_item_id': str(vi.id),
                            'quantity': float(qty),
                            'rate': float(rate)
                        })
                    else:
                        messages.error(request, f'Please enter both quantity and rate for {vi.item.item_name}')
                        break

            if not items_data:
                messages.error(request, 'Please select at least one item with quantity and rate.')
            else:
                try:
                    # Update session company to selected company
                    request.session['company_id'] = str(selected_company.id)

                    # Set the company and loading_point on vehicle before creating sale
                    vehicle.company = selected_company
                    selected_loading_point = form.cleaned_data.get('loading_point')
                    if selected_loading_point:
                        vehicle.loading_point = selected_loading_point
                    vehicle.save(update_fields=['company', 'loading_point'])

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
        form = SaleCreateForm(vehicle_items=vehicle_items, companies=companies, loading_points=loading_points)
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


@login_required
def vehicle_dispatch(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
    
    if vehicle.status != 'Loaded':
        messages.error(request, f"Vehicle must be Loaded to dispatch. Current: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    if request.method == 'POST':
        form = VehicleDispatchForm(request.POST)
        if form.is_valid():
            try:
                vehicle = VehicleService.dispatch_vehicle(vehicle, request.user, request)
                messages.success(request, f'Vehicle {vehicle.vehicle_number} dispatched successfully.')
                return redirect('vehicle_detail', pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = VehicleDispatchForm()
    
    return render(request, 'vehicles/vehicle_dispatch.html', {'vehicle': vehicle, 'form': form})


@login_required
def vehicle_deliver(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # Check authorization
    if vehicle.company_id and vehicle.company_id not in user_company_ids:
        return get_object_or_404(Vehicle, pk=None)
    
    if vehicle.status not in ('InTransit', 'Loaded'):
        messages.error(request, f"Cannot deliver vehicle with status: {vehicle.status}")
        return redirect('vehicle_detail', pk=pk)

    if request.method == 'POST':
        form = VehicleDeliveryForm(request.POST)
        if form.is_valid():
            try:
                vehicle = VehicleService.deliver_vehicle(
                    vehicle=vehicle,
                    delivered_to=form.cleaned_data.get('delivered_to', ''),
                    pod_reference=form.cleaned_data.get('pod_reference', ''),
                    delivery_remarks=form.cleaned_data.get('delivery_remarks', ''),
                    user=request.user,
                    request=request
                )
                messages.success(request, f'Vehicle {vehicle.vehicle_number} marked as delivered.')
                return redirect('vehicle_detail', pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = VehicleDeliveryForm()
    
    return render(request, 'vehicles/vehicle_deliver.html', {'vehicle': vehicle, 'form': form})
