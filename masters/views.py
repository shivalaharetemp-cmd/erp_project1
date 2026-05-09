from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem
from .forms import PartyForm, ItemForm, TransporterForm, PurchaseOrderForm, PurchaseOrderItemFormSet
from core.models import Company, CompanyUser


def _company_id(request):
    return request.session.get('company_id')


# ---- Parties ----
@login_required
def party_list(request):
    # Parties are company-neutral - all users see all parties
    qs = Party.objects.filter(is_active=True).order_by('party_name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(party_name__icontains=search) | qs.filter(party_code__icontains=search) | qs.filter(gstin__icontains=search)
    return render(request, 'masters/party_list.html', {'parties': qs, 'search': search})


@login_required
def party_create(request):
    if request.method == 'POST':
        form = PartyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Party "{form.instance.party_name}" created.')
            return redirect('party_list')
    else:
        form = PartyForm()
    return render(request, 'masters/party_form.html', {'form': form, 'title': 'Create Party'})


@login_required
def party_detail(request, pk):
    party = get_object_or_404(Party, pk=pk)
    
    # Get all sales for this party with vehicle and company details
    from sales.models import Sale
    sales = Sale.objects.filter(party=party).select_related('vehicle', 'company').prefetch_related('items').order_by('-invoice_date')
    
    return render(request, 'masters/party_detail.html', {
        'party': party,
        'sales': sales,
    })


@login_required
def party_edit(request, pk):
    party = get_object_or_404(Party, pk=pk)
    if request.method == 'POST':
        form = PartyForm(request.POST, instance=party)
        if form.is_valid():
            form.save()
            messages.success(request, 'Party updated.')
            return redirect('party_detail', pk=pk)
    else:
        form = PartyForm(instance=party)
    return render(request, 'masters/party_form.html', {'form': form, 'title': 'Edit Party'})


# ---- Items ----
@login_required
def item_list(request):
    # Items are company-neutral - all users see all items
    qs = Item.objects.filter(is_active=True).order_by('item_name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(item_name__icontains=search) | qs.filter(item_code__icontains=search)
    return render(request, 'masters/item_list.html', {'items': qs, 'search': search})


@login_required
def item_create(request):
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{form.instance.item_name}" created.')
            return redirect('item_list')
    else:
        form = ItemForm()
    return render(request, 'masters/item_form.html', {'form': form, 'title': 'Create Item'})


@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, 'masters/item_detail.html', {'item': item})


@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated.')
            return redirect('item_detail', pk=pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'masters/item_form.html', {'form': form, 'title': 'Edit Item'})


# ---- Transporters ----
@login_required
def transporter_list(request):
    # Transporters are company-neutral - all users see all transporters
    qs = Transporter.objects.filter(is_active=True).order_by('name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(name__icontains=search)
    return render(request, 'masters/transporter_list.html', {'transporters': qs, 'search': search})


@login_required
def transporter_create(request):
    if request.method == 'POST':
        form = TransporterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Transporter "{form.instance.name}" created.')
            return redirect('transporter_list')
    else:
        form = TransporterForm()
    return render(request, 'masters/transporter_form.html', {'form': form, 'title': 'Create Transporter'})


@login_required
def transporter_detail(request, pk):
    t = get_object_or_404(Transporter, pk=pk)
    
    # Get all vehicles for this transporter
    from vehicles.models import Vehicle
    vehicles = Vehicle.objects.filter(transporter=t).select_related('party', 'company').order_by('-created_at')
    
    # Get all freights for this transporter (through vehicles)
    from freight.models import Freight
    vehicle_ids = list(vehicles.values_list('id', flat=True))
    
    # Build combined data: one row per freight record with vehicle details
    combined_data = []
    if vehicle_ids:
        freight_list = Freight.objects.filter(vehicle_id__in=vehicle_ids).select_related('vehicle', 'company').order_by('-created_at')
        for freight in freight_list:
            combined_data.append({
                'vehicle': freight.vehicle,
                'freight_type': freight.freight_type,
                'company': freight.company,
                'amount': freight.amount,
                'freight_id': freight.id,
            })
    
    return render(request, 'masters/transporter_detail.html', {
        'transporter': t,
        'combined_data': combined_data,
    })


@login_required
def transporter_edit(request, pk):
    t = get_object_or_404(Transporter, pk=pk)
    if request.method == 'POST':
        form = TransporterForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transporter updated.')
            return redirect('transporter_detail', pk=pk)
    else:
        form = TransporterForm(instance=t)
    return render(request, 'masters/transporter_form.html', {'form': form, 'title': 'Edit Transporter'})


# ---- Purchase Orders ----
@login_required
def po_list(request):
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = PurchaseOrder.objects.filter(company_id__in=user_company_ids).select_related('party', 'company').order_by('-po_date')
    
    # Party filtering
    party_id = request.GET.get('party', '')
    if party_id:
        qs = qs.filter(party_id=party_id)
    
    # Status filtering
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    
    # Search filtering (party name, PO number, etc.)
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(
            Q(party__party_name__icontains=search) |
            Q(party__party_code__icontains=search) |
            Q(po_number__icontains=search)
        ).distinct()
    
    # Get all parties for filter dropdown
    parties = Party.objects.filter(is_active=True).order_by('party_name')
    
    return render(request, 'masters/po_list.html', {
        'purchase_orders': qs,
        'status_filter': status_filter,
        'parties': parties,
        'selected_party': party_id,
        'search': search,
    })


@login_required
def po_create(request):
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        formset = PurchaseOrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()
            formset.instance = po
            formset.save()
            messages.success(request, f'Purchase Order "{po.po_number}" created.')
            return redirect('po_detail', pk=po.id)
    else:
        form = PurchaseOrderForm()
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        formset = PurchaseOrderItemFormSet()
    return render(request, 'masters/po_form.html', {'form': form, 'formset': formset, 'title': 'Create Purchase Order'})


@login_required
def po_detail(request, pk):
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    po = get_object_or_404(PurchaseOrder, pk=pk)
    # Check authorization
    if po.company_id not in user_company_ids:
        return get_object_or_404(PurchaseOrder, pk=None)
    items = po.items.select_related('item').all()
    return render(request, 'masters/po_detail.html', {'po': po, 'po_items': items})


@login_required
def po_edit(request, pk):
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    po = get_object_or_404(PurchaseOrder, pk=pk)
    # Check authorization
    if po.company_id not in user_company_ids:
        return get_object_or_404(PurchaseOrder, pk=None)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        formset = PurchaseOrderItemFormSet(request.POST, instance=po)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Purchase Order updated.')
            return redirect('po_detail', pk=pk)
    else:
        form = PurchaseOrderForm(instance=po)
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        formset = PurchaseOrderItemFormSet(instance=po)
    return render(request, 'masters/po_form.html', {'form': form, 'formset': formset, 'title': 'Edit Purchase Order'})
