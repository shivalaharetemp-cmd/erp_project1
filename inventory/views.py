from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Stock, StockMovement, StockAdjustment
from core.models import CompanyUser


@login_required
def stock_list(request):
    """List current stock for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    stocks = Stock.objects.filter(
        company_id__in=user_company_ids
    ).select_related('item', 'company').order_by('item__item_name')
    
    # Calculate totals
    total_items = stocks.count()
    total_stock_value = sum(s.quantity * 0 for s in stocks)  # Without rate info
    
    return render(request, 'inventory/stock_list.html', {
        'stocks': stocks,
        'total_items': total_items,
    })


@login_required
def stock_detail(request, pk):
    """View stock details and movement history."""
    user_company_ids = list(CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True))
    
    stock = get_object_or_404(Stock, pk=pk)
    
    # Check authorization
    if stock.company_id not in user_company_ids:
        return get_object_or_404(Stock, pk=None)
    
    # Get recent movements
    movements = StockMovement.objects.filter(
        company=stock.company, item=stock.item
    ).select_related('created_by').order_by('-created_at')[:20]
    
    return render(request, 'inventory/stock_detail.html', {
        'stock': stock,
        'movements': movements,
    })


@login_required
def stock_movement_list(request):
    """List all stock movements for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    movements = StockMovement.objects.filter(
        company_id__in=user_company_ids
    ).select_related('item', 'company', 'created_by').order_by('-created_at')
    
    # Filter by movement type if provided
    movement_type = request.GET.get('type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    return render(request, 'inventory/movement_list.html', {
        'movements': movements,
        'type_filter': movement_type,
    })


@login_required
def stock_adjustment_list(request):
    """List stock adjustments for user's companies."""
    user_company_ids = CompanyUser.objects.filter(
        user=request.user, is_active=True
    ).values_list('company_id', flat=True)
    
    adjustments = StockAdjustment.objects.filter(
        company_id__in=user_company_ids
    ).select_related('item', 'company', 'created_by', 'approved_by').order_by('-created_at')
    
    return render(request, 'inventory/adjustment_list.html', {
        'adjustments': adjustments,
    })
