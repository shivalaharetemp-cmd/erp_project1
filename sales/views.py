from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sale, SaleItem, CreditNote, CreditNoteItem
from django.db.models import Sum
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
    
    qs = Sale.objects.filter(company_id__in=user_company_ids).select_related('party', 'vehicle', 'company')
    fy = request.GET.get('fy', '')
    status = request.GET.get('status', '')
    if fy:
        qs = qs.filter(financial_year=fy)
    if status:
        qs = qs.filter(status=status)
    qs = qs.annotate(total_quantity=Sum('items__quantity')).order_by('-invoice_date')
    return render(request, 'sales/sale_list.html', {'sales': qs, 'fy_filter': fy, 'status_filter': status})


@login_required
def sale_detail(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    sale = get_object_or_404(Sale, pk=pk)
    # Check authorization
    if sale.company_id not in user_company_ids:
        return get_object_or_404(Sale, pk=None)
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
    from core.models import CompanyUser
    from django.db.models import Sum
    from .services import TaxCalculationService
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    # Show active sales across all authorized companies
    active_sales = Sale.objects.filter(company_id__in=user_company_ids, status='Active').select_related('party', 'vehicle', 'company')
    # Allow pre-selecting a sale via GET param (used when coming from sale detail)
    initial_sale_id = request.GET.get('sale_id', '')

    # Prepare sales data with remaining creditable amounts and tax info for each item
    sales_data = {}
    for sale in active_sales:
        items = []
        for si in sale.items.select_related('item').all():
            # Calculate already credited amount for this item
            already_credited = CreditNoteItem.objects.filter(
                sale_item=si,
                credit_note__status='Active'
            ).aggregate(total=Sum('amount'))['total'] or 0
            remaining = float(si.amount) - float(already_credited)
            # Get tax info
            tax_info = TaxCalculationService.calculate_tax(si.item, sale.party, sale.company)
            tax_display = 'IGST'
            if tax_info['tax_type'] == 'CGST+SGST':
                tax_display = f"CGST {tax_info['cgst_rate']}% + SGST {tax_info['sgst_rate']}%"
            else:
                tax_display = f"IGST {tax_info['igst_rate']}%"
            items.append({
                'id': str(si.id),
                'item': si.item.item_name,
                'qty': str(si.quantity),
                'rate': str(si.rate),
                'amount': str(si.amount),
                'remaining': str(remaining),
                'already_credited': str(already_credited),
                'tax_display': tax_display,
                'tax_rate': str(si.item.tax_rate),
            })
        sales_data[str(sale.id)] = items

    if request.method == 'POST':
        sale_id = request.POST.get('sale_id')
        if not sale_id:
            messages.error(request, 'Select a sale.')
            return redirect('credit_note_create')

        sale = get_object_or_404(Sale, pk=sale_id, status='Active')
        # Check authorization
        if sale.company_id not in user_company_ids:
            return get_object_or_404(Sale, pk=None)
        sale_items = sale.items.select_related('item').all()

        items_data = []
        for i, si in enumerate(sale_items):
            # Support amount-based partial credit notes (preferred): amount only
            amount_val = request.POST.get(f'amount_{i}', '')
            if amount_val:
                try:
                    amt = float(amount_val)
                except Exception:
                    amt = 0
                if amt > 0:
                    items_data.append({'sale_item_id': str(si.id), 'amount': amt})
                continue

            # Fallback to quantity/rate based inputs (backward compatible)
            qty = float(request.POST.get(f'quantity_{i}', 0))
            rate = float(request.POST.get(f'rate_{i}', 0))
            if qty > 0:
                items_data.append({'sale_item_id': str(si.id), 'quantity': qty, 'rate': rate})

        if not items_data:
            messages.error(request, 'No items specified.')
            return redirect('credit_note_create')

        reason = request.POST.get('reason', '')
        cn_type = request.POST.get('cn_type', 'Full')
        try:
            cn = SaleService.create_credit_note(sale_id, items_data, request.user, reason, request, cn_type)
            messages.success(request, f'Credit Note {cn.credit_note_number} created.')
            return redirect('credit_note_detail', pk=cn.id)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('credit_note_create')

    return render(request, 'sales/credit_note_create.html', {
        'active_sales': active_sales,
        'initial_sale_id': initial_sale_id,
        'sales_data_json': sales_data,
    })


@login_required
def credit_note_detail(request, pk):
    from core.models import CompanyUser
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    cn = get_object_or_404(CreditNote, pk=pk)
    # Check authorization
    if cn.company_id not in user_company_ids:
        return get_object_or_404(CreditNote, pk=None)
    items = cn.items.select_related('item', 'sale_item').all()
    return_freights = cn.return_freights.all()
    return render(request, 'sales/credit_note_detail.html', {
        'credit_note': cn, 'items': items, 'return_freights': return_freights
    })
