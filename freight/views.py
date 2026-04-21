from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import Freight, ReturnFreight
from .forms import FreightForm, ReturnFreightForm


def _company_id(request):
    return request.session.get('company_id')


@login_required
def freight_list(request):
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = Freight.objects.filter(company_id__in=user_company_ids).select_related('vehicle', 'company', 'created_by').order_by('-created_at')
    vehicle_id = request.GET.get('vehicle', '')
    if vehicle_id:
        qs = qs.filter(vehicle_id=vehicle_id)
    return render(request, 'freight/freight_list.html', {'freights': qs, 'vehicle_filter': vehicle_id})


@login_required
def freight_create(request):
    cid = _company_id(request)
    if request.method == 'POST':
        form = FreightForm(request.POST, company_id=cid)
        if form.is_valid():
            freight = form.save(commit=False)
            freight.company_id = cid
            freight.created_by = request.user
            freight.save()
            messages.success(request, f'Freight added for vehicle {freight.vehicle.vehicle_number}.')
            return redirect('freight_by_vehicle', vehicle_id=freight.vehicle.id)
    else:
        form = FreightForm(company_id=cid)
    return render(request, 'freight/freight_form.html', {'form': form, 'title': 'Add Freight'})


@login_required
def freight_update(request, pk):
    cid = _company_id(request)
    freight = get_object_or_404(Freight, pk=pk, company_id=cid)
    
    # Get vehicle item quantity (sum of all vehicle items for this vehicle)
    vehicle_item_qty = freight.vehicle.items.aggregate(
        total_qty=models.Sum('quantity')
    )['total_qty'] or 0
    from decimal import Decimal
    vehicle_item_qty = Decimal(str(vehicle_item_qty))
    
    if request.method == 'POST':
        form = FreightForm(request.POST, instance=freight, company_id=cid, is_edit=True)
        if form.is_valid():
            from freight.services import FreightService
            freight_type = form.cleaned_data.get('freight_type')
            quantity = form.cleaned_data.get('quantity')
            rate = form.cleaned_data.get('rate')
            amount = form.cleaned_data.get('amount')
            
            # For PerQuantity: use vehicle_item_qty (not editable)
            if freight_type == 'PerQuantity':
                quantity = vehicle_item_qty
            # For Guaranteed: use edited quantity
            elif freight_type == 'Guaranteed':
                quantity = quantity if quantity else vehicle_item_qty
            # For Fixed: no quantity needed
            elif freight_type == 'Fixed':
                quantity = None
            
            FreightService.update_freight_and_recalculate_invoice(
                freight_id=freight.id,
                freight_type=freight_type,
                quantity=quantity,
                rate=rate,
                amount=amount,
                user=request.user
            )
            messages.success(request, f'Freight updated for vehicle {freight.vehicle.vehicle_number}.')
            return redirect('freight_by_vehicle', vehicle_id=freight.vehicle.id)
    else:
        form = FreightForm(instance=freight, company_id=cid, is_edit=True)
    
    return render(request, 'freight/freight_form.html', {
        'form': form, 
        'title': 'Edit Freight',
        'freight': freight,
        'vehicle_item_qty': vehicle_item_qty,
    })


@login_required
def freight_by_vehicle(request, vehicle_id):
    cid = _company_id(request)
    from vehicles.models import Vehicle
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id, company_id=cid)
    freights = Freight.objects.filter(vehicle=vehicle, company_id=cid).order_by('-created_at')
    return render(request, 'freight/freight_by_vehicle.html', {'vehicle': vehicle, 'freights': freights})


@login_required
def return_freight_create(request):
    cid = _company_id(request)
    if request.method == 'POST':
        form = ReturnFreightForm(request.POST, company_id=cid)
        if form.is_valid():
            rf = form.save(commit=False)
            rf.company_id = cid
            rf.created_by = request.user
            rf.save()
            messages.success(request, 'Return freight created.')
            return redirect('credit_note_detail', pk=rf.credit_note.id)
    else:
        form = ReturnFreightForm(company_id=cid)
    return render(request, 'freight/return_freight_form.html', {'form': form, 'title': 'Create Return Freight'})


@login_required
def freight_deactivate(request, pk):
    cid = _company_id(request)
    freight = get_object_or_404(Freight, pk=pk, company_id=cid)
    freight.is_active = False
    freight.save()
    messages.success(request, 'Freight deactivated.')
    return redirect('freight_by_vehicle', vehicle_id=freight.vehicle.id)
