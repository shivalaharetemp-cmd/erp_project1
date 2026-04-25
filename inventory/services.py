from django.db import transaction
from decimal import Decimal
from .models import Stock, StockMovement, StockAdjustment


class InventoryService:
    """Service for inventory/stock operations."""

    @staticmethod
    @transaction.atomic
    def add_stock(company, item, quantity, movement_type, reference_no='', reference_date=None,
                  purchase_order=None, sale=None, vehicle=None, created_by=None, remarks=''):
        """Add stock to inventory (IN movement)."""
        stock, created = Stock.objects.select_for_update().get_or_create(
            company=company,
            item=item,
            defaults={'quantity': 0, 'reserved_quantity': 0}
        )
        
        old_qty = stock.quantity
        stock.quantity += Decimal(str(quantity))
        stock.save()

        movement = StockMovement.objects.create(
            company=company,
            item=item,
            movement_type=movement_type,
            quantity=Decimal(str(quantity)),
            reference_no=reference_no,
            reference_date=reference_date,
            purchase_order=purchase_order,
            sale=sale,
            vehicle=vehicle,
            remarks=remarks,
            created_by=created_by
        )

        return stock, movement

    @staticmethod
    @transaction.atomic
    def remove_stock(company, item, quantity, movement_type, reference_no='', reference_date=None,
                     sale=None, vehicle=None, created_by=None, remarks=''):
        """Remove stock from inventory (OUT movement)."""
        stock = Stock.objects.select_for_update().filter(
            company=company, item=item
        ).first()
        
        if not stock:
            raise ValueError(f"No stock found for {item.item_name} in {company.name}")
        
        qty = Decimal(str(quantity))
        if stock.available_quantity < qty:
            raise ValueError(
                f"Insufficient stock for {item.item_name}. "
                f"Available: {stock.available_quantity}, Required: {qty}"
            )
        
        old_qty = stock.quantity
        stock.quantity -= qty
        stock.save()

        movement = StockMovement.objects.create(
            company=company,
            item=item,
            movement_type=movement_type,
            quantity=qty,
            reference_no=reference_no,
            reference_date=reference_date,
            sale=sale,
            vehicle=vehicle,
            remarks=remarks,
            created_by=created_by
        )

        return stock, movement

    @staticmethod
    @transaction.atomic
    def reserve_stock(company, item, quantity):
        """Reserve stock for pending dispatch."""
        stock = Stock.objects.select_for_update().filter(
            company=company, item=item
        ).first()
        
        if not stock:
            raise ValueError(f"No stock found for {item.item_name}")
        
        qty = Decimal(str(quantity))
        if stock.available_quantity < qty:
            raise ValueError(f"Insufficient available stock. Available: {stock.available_quantity}")
        
        stock.reserved_quantity += qty
        stock.save()
        return stock

    @staticmethod
    @transaction.atomic
    def release_reserved_stock(company, item, quantity):
        """Release reserved stock (when sale is cancelled or rejected)."""
        stock = Stock.objects.select_for_update().filter(
            company=company, item=item
        ).first()
        
        if not stock:
            return None
        
        qty = Decimal(str(quantity))
        stock.reserved_quantity = max(0, stock.reserved_quantity - qty)
        stock.save()
        return stock

    @staticmethod
    @transaction.atomic
    def adjust_stock(company, item, new_quantity, adjustment_type, reason, created_by, approved_by=None):
        """Adjust stock for physical count, damage, etc."""
        stock = Stock.objects.select_for_update().filter(
            company=company, item=item
        ).first()
        
        if not stock:
            # Create new stock if none exists
            old_qty = Decimal('0')
            stock = Stock.objects.create(
                company=company,
                item=item,
                quantity=Decimal(str(new_quantity)),
                reserved_quantity=0
            )
        else:
            old_qty = stock.quantity
            stock.quantity = Decimal(str(new_quantity))
            stock.save()
        
        new_qty = Decimal(str(new_quantity))
        difference = new_qty - old_qty

        adjustment = StockAdjustment.objects.create(
            company=company,
            item=item,
            adjustment_type=adjustment_type,
            old_quantity=old_qty,
            new_quantity=new_qty,
            difference=difference,
            reason=reason,
            created_by=created_by,
            approved_by=approved_by,
            approved_at=approved_by.created_at if approved_by else None
        )

        # Create movement record for the adjustment
        movement_type = 'IN_ADJUSTMENT' if difference > 0 else 'OUT_ADJUSTMENT'
        StockMovement.objects.create(
            company=company,
            item=item,
            movement_type=movement_type,
            quantity=abs(difference),
            remarks=f"Stock Adjustment: {adjustment_type} - {reason}",
            created_by=created_by
        )

        return stock, adjustment

    @staticmethod
    def get_stock_summary(company):
        """Get complete stock summary for a company."""
        stocks = Stock.objects.filter(company=company).select_related('item')
        return {
            'total_items': stocks.count(),
            'total_quantity': sum(s.quantity for s in stocks),
            'total_reserved': sum(s.reserved_quantity for s in stocks),
            'low_stock_items': [s for s in stocks if s.available_quantity < 10],  # configurable threshold
            'stocks': stocks
        }

    @staticmethod
    def get_item_movements(company, item, limit=50):
        """Get recent movements for an item."""
        return StockMovement.objects.filter(
            company=company, item=item
        ).order_by('-created_at')[:limit]

    @staticmethod
    def process_sale_dispatch(sale, user):
        """Process stock dispatch when vehicle is loaded and invoice created."""
        company = sale.company
        movements = []
        
        for sale_item in sale.items.all():
            item = sale_item.item
            quantity = sale_item.quantity
            
            # Release reserved and deduct actual stock
            try:
                stock, movement = InventoryService.remove_stock(
                    company=company,
                    item=item,
                    quantity=quantity,
                    movement_type='OUT_SALE',
                    reference_no=sale.invoice_number,
                    reference_date=sale.invoice_date,
                    sale=sale,
                    vehicle=sale.vehicle,
                    created_by=user,
                    remarks=f"Sale invoice dispatch: {sale.invoice_number}"
                )
                movements.append(movement)
            except ValueError as e:
                # Log error but continue - this shouldn't happen if reservations work properly
                print(f"Stock error for {item.item_name}: {e}")
                raise
        
        return movements

    @staticmethod
    def process_credit_note_receipt(credit_note, user):
        """Process stock receipt when credit note is created (return of goods)."""
        if credit_note.cn_type == 'Value':
            # Value credit notes don't involve physical return
            return []
        
        company = credit_note.company
        movements = []
        
        for cn_item in credit_note.items.all():
            if cn_item.quantity > 0:  # Physical return
                item = cn_item.item
                quantity = cn_item.quantity
                
                stock, movement = InventoryService.add_stock(
                    company=company,
                    item=item,
                    quantity=quantity,
                    movement_type='IN_RETURN',
                    reference_no=credit_note.credit_note_number,
                    reference_date=credit_note.credit_note_date,
                    sale=credit_note.sale,
                    created_by=user,
                    remarks=f"Credit note return: {credit_note.credit_note_number} ({credit_note.cn_type})"
                )
                movements.append(movement)
        
        return movements

    @staticmethod
    def process_purchase_receipt(po_item, received_quantity, user, remarks=''):
        """Process stock receipt from purchase order."""
        po = po_item.purchase_order
        company = po.company
        item = po_item.item
        
        stock, movement = InventoryService.add_stock(
            company=company,
            item=item,
            quantity=received_quantity,
            movement_type='IN_PURCHASE',
            reference_no=po.po_number,
            reference_date=po.po_date,
            purchase_order=po,
            created_by=user,
            remarks=remarks or f"Purchase receipt: {po.po_number}"
        )
        
        # Update PO fulfilled quantity
        po_item.fulfilled_quantity += Decimal(str(received_quantity))
        po_item.save()
        
        # Check if PO is fully fulfilled
        total_qty = sum(i.quantity for i in po.items.all())
        fulfilled_qty = sum(i.fulfilled_quantity for i in po.items.all())
        if fulfilled_qty >= total_qty:
            po.status = 'Fulfilled'
        elif fulfilled_qty > 0:
            po.status = 'Partially Fulfilled'
        po.save()
        
        return stock, movement
