from decimal import Decimal
from .models import Freight


class FreightService:
    """Service for freight operations."""

    @staticmethod
    def calculate_freight_amount(freight_type, quantity=None, rate=None, amount=None):
        """
        Calculate freight amount based on type.
        - PerQuantity: quantity * rate
        - Fixed: amount (provided directly)
        - Guaranteed: quantity * rate
        """
        if freight_type in ['PerQuantity', 'Guaranteed']:
            if quantity and rate:
                return Decimal(str(quantity)) * Decimal(str(rate))
            return Decimal('0')
        elif freight_type == 'Fixed':
            return Decimal(str(amount)) if amount else Decimal('0')
        return Decimal('0')

    @staticmethod
    def create_freight_from_sale(vehicle, company, freight_type, quantity, rate, amount, user):
        """
        Create a provisional freight entry from sales invoice.
        """
        # Calculate amount if not provided
        if not amount or amount == Decimal('0'):
            amount = FreightService.calculate_freight_amount(freight_type, quantity, rate, amount)

        freight = Freight.objects.create(
            vehicle=vehicle,
            company=company,
            freight_type=freight_type,
            quantity=quantity if freight_type != 'Fixed' else None,
            rate=rate if freight_type != 'Fixed' else None,
            amount=amount,
            created_by=user,
        )
        return freight

    @staticmethod
    def update_freight_and_recalculate_invoice(freight_id, freight_type, quantity, rate, amount, user):
        """
        Update freight entry and recalculate invoice grand total if sale exists.
        """
        from sales.models import Sale
        
        freight = Freight.objects.get(id=freight_id)
        
        # Calculate new amount
        new_amount = FreightService.calculate_freight_amount(freight_type, quantity, rate, amount)
        
        # Update freight
        freight.freight_type = freight_type
        freight.quantity = quantity if freight_type != 'Fixed' else None
        freight.rate = rate if freight_type != 'Fixed' else None
        freight.amount = new_amount
        freight.save()
        
        # Recalculate sale grand_total if this vehicle has an invoice
        try:
            sale = Sale.objects.get(vehicle=freight.vehicle)
            # Recalculate with new freight amount
            sale.grand_total = sale.subtotal + sale.total_tax + new_amount
            sale.save()
        except Sale.DoesNotExist:
            pass
        
        return freight

