from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sale, SaleItem, CreditNote, CreditNoteItem
from .services import SaleService


def _company_id(request):
    return request.session.get('company_id')


@login_required
def sale_list(request):
    # Get all companies for this user
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    qs = Sale.objects.filter(company_id__in=user_company_ids).select_related('party', 'vehicle', 'company').order_by('-invoice_date')
    fy = request.GET.get('fy', '')
    status = request.GET.get('status', '')
    if fy:
        qs = qs.filter(financial_year=fy)
    if status:
        qs = qs.filter(status=status)
    return render(request, 'sales/sale_list.html', {'sales': qs, 'fy_filter': fy, 'status_filter': status})


@login_required
def sale_detail(request, pk):
    cid = _company_id(request)
    sale = get_object_or_404(Sale, pk=pk, company_id=cid)
    items = sale.items.select_related('item').all()
    freights = sale.vehicle.freights.filter(is_active=True).order_by('-created_at')
    return render(request, 'sales/sale_detail.html', {'sale': sale, 'items': items, 'freights': freights})


@login_required
def credit_note_list(request):
    from core.models import CompanyUser
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    qs = CreditNote.objects.filter(company_id__in=user_company_ids).select_related('party', 'sale', 'vehicle', 'company').order_by('-credit_note_date')
    return render(request, 'sales/credit_note_list.html', {'credit_notes': qs})


@login_required
def credit_note_create(request):
    cid = _company_id(request)
    active_sales = Sale.objects.filter(company_id=cid, status='Active').select_related('party', 'vehicle')

    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        if not sale_id:
            messages.error(request, 'Select a sale.')
            return redirect('credit_note_create')

        sale = get_object_or_404(Sale, pk=sale_id, company_id=cid, status='Active')
        sale_items = sale.items.select_related('item').all()

        items_data = []
        for i, si in enumerate(sale_items):
            qty = float(request.POST.get(f'quantity_{i}', 0))
            rate = float(request.POST.get(f'rate_{i}', 0))
            if qty > 0:
                items_data.append({'sale_item_id': str(si.id), 'quantity': qty, 'rate': rate})

        if not items_data:
            messages.error(request, 'No items specified.')
            return redirect('credit_note_create')

        reason = request.POST.get('reason', '')
        try:
            cn = SaleService.create_credit_note(sale_id, items_data, request.user, reason, request)
            messages.success(request, f'Credit Note {cn.credit_note_number} created.')
            return redirect('credit_note_detail', pk=cn.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('credit_note_create')

    return render(request, 'sales/credit_note_create.html', {'active_sales': active_sales})


@login_required
def credit_note_detail(request, pk):
    cid = _company_id(request)
    cn = get_object_or_404(CreditNote, pk=pk, company_id=cid)
    items = cn.items.select_related('item', 'sale_item').all()
    return_freights = cn.return_freights.all()
    return render(request, 'sales/credit_note_detail.html', {
        'credit_note': cn, 'items': items, 'return_freights': return_freights
    })
