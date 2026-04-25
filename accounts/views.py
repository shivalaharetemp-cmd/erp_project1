from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from .models import AccountReceivable, AccountPayable, LedgerEntry, TransporterBill, Receipt, Payment
from .services import AccountingService
from .forms import ReceiptForm, PaymentForm
from core.models import CompanyUser


@login_required
def receivable_list(request):
    """List all account receivables for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    receivables = AccountReceivable.objects.filter(
        company_id__in=user_company_ids
    ).select_related('party', 'company', 'sale').order_by('-invoice_date')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        receivables = receivables.filter(status=status)
    
    # Calculate totals
    total_pending = sum(r.balance_amount for r in receivables.filter(status__in=['UNPAID', 'PARTIAL', 'OVERDUE']))
    
    return render(request, 'accounts/receivable_list.html', {
        'receivables': receivables,
        'status_filter': status,
        'total_pending': total_pending,
    })


@login_required
def receivable_detail(request, pk):
    """View receivable details with receipt history."""
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    
    if receivable.company_id not in user_company_ids:
        return get_object_or_404(AccountReceivable, pk=None)
    
    receipts = receivable.receipts.all().order_by('-receipt_date')
    
    return render(request, 'accounts/receivable_detail.html', {
        'receivable': receivable,
        'receipts': receipts,
    })


@login_required
def add_receipt(request, pk):
    """Add receipt against a receivable."""
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    
    receivable = get_object_or_404(AccountReceivable, pk=pk)
    
    if receivable.company_id not in user_company_ids:
        return get_object_or_404(AccountReceivable, pk=None)
    
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        if form.is_valid():
            try:
                AccountingService.record_receipt(
                    receivable=receivable,
                    amount=form.cleaned_data['amount'],
                    payment_mode=form.cleaned_data['payment_mode'],
                    reference_number=form.cleaned_data['reference_number'],
                    user=request.user,
                    remarks=form.cleaned_data['remarks'],
                )
                messages.success(request, f"Receipt of {form.cleaned_data['amount']} recorded successfully.")
                return redirect('receivable_detail', pk=pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        # Pre-fill with remaining balance
        form = ReceiptForm(initial={'amount': receivable.balance_amount})
    
    return render(request, 'accounts/add_receipt.html', {
        'receivable': receivable,
        'form': form,
    })


@login_required
def payable_list(request):
    """List all account payables for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    payables = AccountPayable.objects.filter(
        company_id__in=user_company_ids
    ).select_related('party', 'transporter', 'company').order_by('-bill_date')
    
    # Filter by status and type
    status = request.GET.get('status', '')
    ptype = request.GET.get('type', '')
    
    if status:
        payables = payables.filter(status=status)
    if ptype:
        payables = payables.filter(payable_type=ptype)
    
    # Calculate totals
    total_pending = sum(p.balance_amount for p in payables.filter(status__in=['UNPAID', 'PARTIAL', 'OVERDUE']))
    
    return render(request, 'accounts/payable_list.html', {
        'payables': payables,
        'status_filter': status,
        'type_filter': ptype,
        'total_pending': total_pending,
    })


@login_required
def payable_detail(request, pk):
    """View payable details with payment history."""
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    
    payable = get_object_or_404(AccountPayable, pk=pk)
    
    if payable.company_id not in user_company_ids:
        return get_object_or_404(AccountPayable, pk=None)
    
    payments = payable.payments.all().order_by('-payment_date')
    
    return render(request, 'accounts/payable_detail.html', {
        'payable': payable,
        'payments': payments,
    })


@login_required
def add_payment(request, pk):
    """Add payment against a payable."""
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    
    payable = get_object_or_404(AccountPayable, pk=pk)
    
    if payable.company_id not in user_company_ids:
        return get_object_or_404(AccountPayable, pk=None)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                AccountingService.record_payment(
                    payable=payable,
                    amount=form.cleaned_data['amount'],
                    payment_mode=form.cleaned_data['payment_mode'],
                    reference_number=form.cleaned_data['reference_number'],
                    user=request.user,
                    remarks=form.cleaned_data['remarks'],
                )
                messages.success(request, f"Payment of {form.cleaned_data['amount']} recorded successfully.")
                return redirect('payable_detail', pk=pk)
            except Exception as e:
                messages.error(request, str(e))
    else:
        # Pre-fill with remaining balance
        form = PaymentForm(initial={'amount': payable.balance_amount})
    
    return render(request, 'accounts/add_payment.html', {
        'payable': payable,
        'form': form,
    })


@login_required
def ledger_list(request):
    """View ledger entries for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    entries = LedgerEntry.objects.filter(
        company_id__in=user_company_ids
    ).select_related('account', 'company', 'created_by').order_by('-entry_date', '-created_at')
    
    # Filter by voucher type
    vtype = request.GET.get('type', '')
    if vtype:
        entries = entries.filter(voucher_type=vtype)
    
    return render(request, 'accounts/ledger_list.html', {
        'entries': entries,
        'type_filter': vtype,
    })


@login_required
def transporter_bill_list(request):
    """List transporter bills for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    bills = TransporterBill.objects.filter(
        company_id__in=user_company_ids
    ).select_related('transporter', 'company').order_by('-bill_date')
    
    # Filter by status
    status = request.GET.get('status', '')
    if status:
        bills = bills.filter(status=status)
    
    return render(request, 'accounts/transporter_bill_list.html', {
        'bills': bills,
        'status_filter': status,
    })
