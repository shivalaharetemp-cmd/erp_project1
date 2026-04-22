from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem
from .forms import PartyForm, ItemForm, TransporterForm, PurchaseOrderForm, PurchaseOrderItemFormSet


def _company_id(request):
    return request.session.get('company_id')


# ---- Parties ----
@login_required
def party_list(request):
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = Party.objects.filter(company_id__in=user_company_ids).select_related('company').order_by('party_name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(party_name__icontains=search) | qs.filter(party_code__icontains=search) | qs.filter(gstin__icontains=search)
    return render(request, 'masters/party_list.html', {'parties': qs, 'search': search})


@login_required
def party_create(request):
    from core.models import Company
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    if request.method == 'POST':
        form = PartyForm(request.POST)
        # Filter company choices to user's companies only
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        if form.is_valid():
            form.save()
            messages.success(request, f'Party "{form.instance.party_name}" created.')
            return redirect('party_list')
    else:
        form = PartyForm()
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
    return render(request, 'masters/party_form.html', {'form': form, 'title': 'Create Party'})


@login_required
def party_detail(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    party = get_object_or_404(Party, pk=pk)
    # Check authorization
    if party.company_id not in user_company_ids:
        return get_object_or_404(Party, pk=None)
    return render(request, 'masters/party_detail.html', {'party': party})


@login_required
def party_edit(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    party = get_object_or_404(Party, pk=pk)
    # Check authorization
    if party.company_id not in user_company_ids:
        return get_object_or_404(Party, pk=None)
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
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = Item.objects.filter(company_id__in=user_company_ids).select_related('company').order_by('item_name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(item_name__icontains=search) | qs.filter(item_code__icontains=search)
    return render(request, 'masters/item_list.html', {'items': qs, 'search': search})


@login_required
def item_create(request):
    from core.models import Company
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    if request.method == 'POST':
        form = ItemForm(request.POST)
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        if form.is_valid():
            form.save()
            messages.success(request, f'Item "{form.instance.item_name}" created.')
            return redirect('item_list')
    else:
        form = ItemForm()
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
    return render(request, 'masters/item_form.html', {'form': form, 'title': 'Create Item'})


@login_required
def item_detail(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    item = get_object_or_404(Item, pk=pk)
    # Check authorization
    if item.company_id not in user_company_ids:
        return get_object_or_404(Item, pk=None)
    return render(request, 'masters/item_detail.html', {'item': item})


@login_required
def item_edit(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    item = get_object_or_404(Item, pk=pk)
    # Check authorization
    if item.company_id not in user_company_ids:
        return get_object_or_404(Item, pk=None)
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
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = Transporter.objects.filter(company_id__in=user_company_ids).select_related('company').order_by('name')
    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(name__icontains=search)
    return render(request, 'masters/transporter_list.html', {'transporters': qs, 'search': search})


@login_required
def transporter_create(request):
    from core.models import Company
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    if request.method == 'POST':
        form = TransporterForm(request.POST)
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
        if form.is_valid():
            form.save()
            messages.success(request, f'Transporter "{form.instance.name}" created.')
            return redirect('transporter_list')
    else:
        form = TransporterForm()
        form.fields['company'].queryset = Company.objects.filter(id__in=user_company_ids)
    return render(request, 'masters/transporter_form.html', {'form': form, 'title': 'Create Transporter'})


@login_required
def transporter_detail(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    t = get_object_or_404(Transporter, pk=pk)
    # Check authorization
    if t.company_id not in user_company_ids:
        return get_object_or_404(Transporter, pk=None)
    return render(request, 'masters/transporter_detail.html', {'transporter': t})


@login_required
def transporter_edit(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    t = get_object_or_404(Transporter, pk=pk)
    # Check authorization
    if t.company_id not in user_company_ids:
        return get_object_or_404(Transporter, pk=None)
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
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = PurchaseOrder.objects.filter(company_id__in=user_company_ids).select_related('party', 'company').order_by('-po_date')
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(request, 'masters/po_list.html', {'purchase_orders': qs, 'status_filter': status_filter})


@login_required
def po_create(request):
    from core.models import Company
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
    from core.models import CompanyUser
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
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    po = get_object_or_404(PurchaseOrder, pk=pk)
    # Check authorization
    if po.company_id not in user_company_ids:
        return get_object_or_404(PurchaseOrder, pk=None)
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderItemFormSet(request.POST, instance=po)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Purchase Order updated.')
            return redirect('po_detail', pk=pk)
    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderItemFormSet(instance=po)
    return render(request, 'masters/po_form.html', {'form': form, 'formset': formset, 'title': 'Edit Purchase Order'})
