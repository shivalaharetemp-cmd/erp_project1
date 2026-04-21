from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Sale, SaleItem, InvoiceNumberSequence, CreditNote, CreditNoteItem, CreditNoteNumberSequence
from audit.services import AuditService


class TaxCalculationService:
    """Service for GST tax calculation."""

    @staticmethod
    def calculate_tax(item, party, company):
        """
        Calculate tax based on party state vs company state.
        Same state: CGST (50%) + SGST (50%)
        Different state: IGST (100%)
        """
        tax_rate = item.tax_rate
        if party.state_code == company.state_code:
            # Same state
            cgst = tax_rate / Decimal('2')
            sgst = tax_rate / Decimal('2')
            return {
                'tax_type': 'CGST+SGST',
                'cgst_rate': cgst,
                'sgst_rate': sgst,
                'igst_rate': Decimal('0'),
            }
        else:
            # Different state
            return {
                'tax_type': 'IGST',
                'cgst_rate': Decimal('0'),
                'sgst_rate': Decimal('0'),
                'igst_rate': tax_rate,
            }

    @staticmethod
    def calculate_item_tax(item, quantity, rate, party, company):
        """Calculate tax amounts for a single line item."""
        amount = quantity * rate
        tax_info = TaxCalculationService.calculate_tax(item, party, company)

        cgst_amount = (amount * tax_info['cgst_rate']) / Decimal('100') if tax_info['cgst_rate'] else Decimal('0')
        sgst_amount = (amount * tax_info['sgst_rate']) / Decimal('100') if tax_info['sgst_rate'] else Decimal('0')
        igst_amount = (amount * tax_info['igst_rate']) / Decimal('100') if tax_info['igst_rate'] else Decimal('0')

        return {
            'amount': amount,
            'cgst_amount': cgst_amount,
            'sgst_amount': sgst_amount,
            'igst_amount': igst_amount,
            'total_tax': cgst_amount + sgst_amount + igst_amount,
            'tax_info': tax_info,
        }


class InvoiceNumberingService:
    """Service for generating sequential invoice/credit note numbers."""

    @staticmethod
    def generate_invoice_number(company):
        """Generate next invoice number: INV/{CompanyCode}/{FinancialYear}/{Sequence}"""
        fy = company.financial_year
        with transaction.atomic():
            seq, created = InvoiceNumberSequence.objects.select_for_update().get_or_create(
                company=company, financial_year=fy,
                defaults={'last_number': 0}
            )
            seq.last_number += 1
            seq.save()
            return f"INV/{company.code}/{fy}/{seq.last_number:06d}"

    @staticmethod
    def generate_credit_note_number(company):
        """Generate next credit note number: CN/{CompanyCode}/{FinancialYear}/{Sequence}"""
        fy = company.financial_year
        with transaction.atomic():
            seq, created = CreditNoteNumberSequence.objects.select_for_update().get_or_create(
                company=company, financial_year=fy,
                defaults={'last_number': 0}
            )
            seq.last_number += 1
            seq.save()
            return f"CN/{company.code}/{fy}/{seq.last_number:06d}"


class SaleService:
    """Service for sale/invoice operations."""

    @staticmethod
    @transaction.atomic
    def create_sale(vehicle, items_data, user, request=None):
        """
        Create sale from vehicle.
        items_data: [{'vehicle_item_id': uuid, 'rate': decimal}]
        Automatically creates a provisional freight entry from vehicle's transporter.
        """
        company = vehicle.company
        party = vehicle.party

        # Check if sale already exists
        if hasattr(vehicle, 'sale') and vehicle.sale:
            raise ValueError("Sale already exists for this vehicle.")

        # Generate invoice number
        invoice_number = InvoiceNumberingService.generate_invoice_number(company)

        sale = Sale.objects.create(
            vehicle=vehicle,
            company=company,
            party=party,
            invoice_number=invoice_number,
            financial_year=company.financial_year,
            created_by=user,
        )

        subtotal = Decimal('0')
        total_cgst = Decimal('0')
        total_sgst = Decimal('0')
        total_igst = Decimal('0')

        for item_data in items_data:
            vehicle_item_id = item_data['vehicle_item_id']
            rate = Decimal(str(item_data['rate']))

            try:
                vehicle_item = vehicle.items.get(id=vehicle_item_id)
            except Exception:
                raise ValueError(f"Vehicle item {vehicle_item_id} not found.")

            item = vehicle_item.item
            quantity = vehicle_item.quantity

            # Calculate tax
            tax_result = TaxCalculationService.calculate_item_tax(
                item, quantity, rate, party, company
            )

            SaleItem.objects.create(
                sale=sale,
                item=item,
                vehicle_item=vehicle_item,
                quantity=quantity,
                rate=rate,
                amount=tax_result['amount'],
                tax_rate=item.tax_rate,
                tax_type=tax_result['tax_info']['tax_type'],
                cgst_amount=tax_result['cgst_amount'],
                sgst_amount=tax_result['sgst_amount'],
                igst_amount=tax_result['igst_amount'],
                hsn_code=item.hsn_code,
            )

            subtotal += tax_result['amount']
            total_cgst += tax_result['cgst_amount']
            total_sgst += tax_result['sgst_amount']
            total_igst += tax_result['igst_amount']

        # Automatically create provisional freight from vehicle's transporter
        freight_amount = Decimal('0')
        if vehicle.transporter:
            from freight.services import FreightService
            freight = FreightService.create_freight_from_sale(
                vehicle=vehicle,
                company=company,
                freight_type='PerQuantity',  # Default type, user can edit
                quantity=None,  # Will be filled by user during edit
                rate=None,      # Will be filled by user during edit
                amount=Decimal('0'),  # Start with 0, user will add rate/amount
                user=user,
            )
            freight_amount = freight.amount

        total_tax = total_cgst + total_sgst + total_igst
        grand_total = subtotal + total_tax + freight_amount

        sale.subtotal = subtotal
        sale.cgst_amount = total_cgst
        sale.sgst_amount = total_sgst
        sale.igst_amount = total_igst
        sale.total_tax = total_tax
        sale.grand_total = grand_total
        sale.save()

        # Audit log
        if request:
            AuditService.log(
                user=user,
                company=company,
                action='GENERATE_INVOICE',
                model_name='Sale',
                object_id=str(sale.id),
                new_value={
                    'invoice_number': sale.invoice_number,
                    'grand_total': str(grand_total),
                },
                request=request,
            )

        return sale

    @staticmethod
    @transaction.atomic
    def create_credit_note(sale_id, items_data, user, reason='', request=None):
        """
        Create credit note to reverse a sale.
        items_data: [{'sale_item_id': uuid, 'quantity': decimal, 'rate': decimal(optional)}]
        """
        try:
            sale = Sale.objects.select_related('vehicle', 'party', 'company').get(id=sale_id)
        except Sale.DoesNotExist:
            raise ValueError("Sale not found.")

        if sale.status == 'Cancelled':
            raise ValueError("Sale is already cancelled.")

        company = sale.company
        vehicle = sale.vehicle

        # Generate credit note number
        cn_number = InvoiceNumberingService.generate_credit_note_number(company)

        credit_note = CreditNote.objects.create(
            sale=sale,
            vehicle=vehicle,
            company=company,
            party=sale.party,
            credit_note_number=cn_number,
            financial_year=company.financial_year,
            reason=reason,
            created_by=user,
        )

        subtotal = Decimal('0')
        total_cgst = Decimal('0')
        total_sgst = Decimal('0')
        total_igst = Decimal('0')

        for item_data in items_data:
            sale_item_id = item_data['sale_item_id']
            cn_quantity = Decimal(str(item_data['quantity']))
            cn_rate = Decimal(str(item_data['rate'])) if item_data.get('rate') else None

            try:
                sale_item = sale.items.get(id=sale_item_id)
            except SaleItem.DoesNotExist:
                raise ValueError(f"Sale item {sale_item_id} not found.")

            # Validate quantity
            if cn_quantity > sale_item.quantity:
                raise ValueError("Credit note quantity cannot exceed original quantity.")

            if cn_rate is None:
                cn_rate = sale_item.rate

            item = sale_item.item
            tax_info = TaxCalculationService.calculate_tax(item, sale.party, company)

            amount = cn_quantity * cn_rate
            cgst_amount = (amount * tax_info['cgst_rate']) / Decimal('100') if tax_info['cgst_rate'] else Decimal('0')
            sgst_amount = (amount * tax_info['sgst_rate']) / Decimal('100') if tax_info['sgst_rate'] else Decimal('0')
            igst_amount = (amount * tax_info['igst_rate']) / Decimal('100') if tax_info['igst_rate'] else Decimal('0')

            CreditNoteItem.objects.create(
                credit_note=credit_note,
                sale_item=sale_item,
                item=item,
                quantity=cn_quantity,
                rate=cn_rate,
                amount=amount,
                tax_rate=sale_item.tax_rate,
                tax_type=tax_info['tax_type'],
                cgst_amount=cgst_amount,
                sgst_amount=sgst_amount,
                igst_amount=igst_amount,
                hsn_code=sale_item.hsn_code,
            )

            subtotal += amount
            total_cgst += cgst_amount
            total_sgst += sgst_amount
            total_igst += igst_amount

        total_tax = total_cgst + total_sgst + total_igst
        grand_total = subtotal + total_tax

        credit_note.subtotal = subtotal
        credit_note.cgst_amount = total_cgst
        credit_note.sgst_amount = total_sgst
        credit_note.igst_amount = total_igst
        credit_note.total_tax = total_tax
        credit_note.grand_total = grand_total
        credit_note.save()

        # Mark original sale as cancelled
        sale.status = 'Cancelled'
        sale.save()

        # Audit
        if request:
            AuditService.log(
                user=user,
                company=company,
                action='GENERATE_CREDIT_NOTE',
                model_name='CreditNote',
                object_id=str(credit_note.id),
                new_value={
                    'credit_note_number': cn_number,
                    'original_invoice': sale.invoice_number,
                    'grand_total': str(grand_total),
                },
                reason=reason,
                request=request,
            )

        return credit_note
