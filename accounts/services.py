from django.db import transaction
from decimal import Decimal
from .models import (
    LedgerAccount, LedgerEntry, AccountReceivable, AccountPayable,
    Receipt, Payment, TransporterBill, TransporterBillPayment
)


class AccountingService:
    """Service for managing accounting entries, receivables, and payables."""

    @staticmethod
    @transaction.atomic
    def create_receivable_from_sale(sale, user):
        """Create account receivable when sale invoice is generated."""
        # Calculate due date based on party payment terms
        from datetime import timedelta
        from django.utils import timezone
        
        due_date = sale.invoice_date + timedelta(days=sale.party.payment_terms)
        
        receivable = AccountReceivable.objects.create(
            company=sale.company,
            party=sale.party,
            sale=sale,
            invoice_number=sale.invoice_number,
            invoice_date=sale.invoice_date,
            due_date=due_date,
            total_amount=sale.grand_total,
            balance_amount=sale.grand_total,
        )
        
        # Create ledger entry
        AccountingService._create_sale_ledger_entries(sale, user)
        
        return receivable

    @staticmethod
    def _create_sale_ledger_entries(sale, user):
        """Create double-entry ledger records for a sale."""
        from django.utils import timezone
        
        # Get or create ledger accounts
        sales_account, _ = LedgerAccount.objects.get_or_create(
            company=sale.company,
            code='SALES',
            defaults={
                'name': 'Sales Revenue',
                'account_type': 'INCOME',
            }
        )
        
        debtors_account, _ = LedgerAccount.objects.get_or_create(
            company=sale.company,
            code='DEBTORS',
            defaults={
                'name': 'Sundry Debtors',
                'account_type': 'ASSET',
            }
        )
        
        cgst_account, _ = LedgerAccount.objects.get_or_create(
            company=sale.company,
            code='CGST-PAYABLE',
            defaults={
                'name': 'CGST Payable',
                'account_type': 'LIABILITY',
            }
        )
        
        sgst_account, _ = LedgerAccount.objects.get_or_create(
            company=sale.company,
            code='SGST-PAYABLE',
            defaults={
                'name': 'SGST Payable',
                'account_type': 'LIABILITY',
            }
        )
        
        igst_account, _ = LedgerAccount.objects.get_or_create(
            company=sale.company,
            code='IGST-PAYABLE',
            defaults={
                'name': 'IGST Payable',
                'account_type': 'LIABILITY',
            }
        )
        
        # Debtor entry (debit)
        LedgerEntry.objects.create(
            company=sale.company,
            entry_date=sale.invoice_date,
            voucher_type='SALE',
            voucher_number=sale.invoice_number,
            sale=sale,
            account=debtors_account,
            party=sale.party,
            debit=sale.grand_total,
            credit=0,
            narration=f"Sale invoice {sale.invoice_number} to {sale.party.party_name}",
            created_by=user,
        )
        
        # Sales entry (credit)
        LedgerEntry.objects.create(
            company=sale.company,
            entry_date=sale.invoice_date,
            voucher_type='SALE',
            voucher_number=sale.invoice_number,
            sale=sale,
            account=sales_account,
            party=sale.party,
            debit=0,
            credit=sale.subtotal,
            narration=f"Sales revenue for {sale.invoice_number}",
            created_by=user,
        )
        
        # Tax entries
        if sale.cgst_amount > 0:
            LedgerEntry.objects.create(
                company=sale.company,
                entry_date=sale.invoice_date,
                voucher_type='SALE',
                voucher_number=sale.invoice_number,
                sale=sale,
                account=cgst_account,
                debit=0,
                credit=sale.cgst_amount,
                narration=f"CGST on {sale.invoice_number}",
                created_by=user,
            )
        
        if sale.sgst_amount > 0:
            LedgerEntry.objects.create(
                company=sale.company,
                entry_date=sale.invoice_date,
                voucher_type='SALE',
                voucher_number=sale.invoice_number,
                sale=sale,
                account=sgst_account,
                debit=0,
                credit=sale.sgst_amount,
                narration=f"SGST on {sale.invoice_number}",
                created_by=user,
            )
        
        if sale.igst_amount > 0:
            LedgerEntry.objects.create(
                company=sale.company,
                entry_date=sale.invoice_date,
                voucher_type='SALE',
                voucher_number=sale.invoice_number,
                sale=sale,
                account=igst_account,
                debit=0,
                credit=sale.igst_amount,
                narration=f"IGST on {sale.invoice_number}",
                created_by=user,
            )

    @staticmethod
    @transaction.atomic
    def record_receipt(receivable, amount, payment_mode, reference_number, user, remarks=''):
        """Record receipt from customer and update receivable."""
        from django.utils import timezone
        
        receipt = Receipt.objects.create(
            company=receivable.company,
            receivable=receivable,
            receipt_date=timezone.now().date(),
            amount=amount,
            payment_mode=payment_mode,
            reference_number=reference_number,
            remarks=remarks,
            created_by=user,
        )
        
        # Create ledger entry for receipt
        bank_account, _ = LedgerAccount.objects.get_or_create(
            company=receivable.company,
            code='BANK',
            defaults={
                'name': 'Bank Account',
                'account_type': 'ASSET',
            }
        )
        
        debtors_account, _ = LedgerAccount.objects.get_or_create(
            company=receivable.company,
            code='DEBTORS',
            defaults={
                'name': 'Sundry Debtors',
                'account_type': 'ASSET',
            }
        )
        
        # Bank entry (debit)
        LedgerEntry.objects.create(
            company=receivable.company,
            entry_date=receipt.receipt_date,
            voucher_type='RECEIPT',
            voucher_number=reference_number or f"RCPT-{receipt.id}",
            account=bank_account,
            party=receivable.party,
            debit=amount,
            credit=0,
            narration=f"Receipt from {receivable.party.party_name} for {receivable.invoice_number}",
            created_by=user,
        )
        
        # Debtor entry (credit - reducing debtor)
        LedgerEntry.objects.create(
            company=receivable.company,
            entry_date=receipt.receipt_date,
            voucher_type='RECEIPT',
            voucher_number=reference_number or f"RCPT-{receipt.id}",
            account=debtors_account,
            party=receivable.party,
            debit=0,
            credit=amount,
            narration=f"Receipt from {receivable.party.party_name}",
            created_by=user,
        )
        
        return receipt

    @staticmethod
    @transaction.atomic
    def create_payable_for_freight(freight, user):
        """Create account payable for freight charges."""
        from datetime import timedelta
        from django.utils import timezone
        import logging
        logger = logging.getLogger(__name__)

        # Check if vehicle has transporter
        if not freight.vehicle.transporter:
            logger.warning(f"Cannot create payable for freight {freight.id}: Vehicle {freight.vehicle.vehicle_number} has no transporter")
            raise ValueError(f"Vehicle {freight.vehicle.vehicle_number} has no transporter assigned")

        # Check if payable already exists
        existing = AccountPayable.objects.filter(freight=freight).first()
        if existing:
            logger.info(f"Payable already exists for freight {freight.id}")
            return existing

        # Default 15 days payment term for transporters
        due_date = timezone.now().date() + timedelta(days=15)

        payable = AccountPayable.objects.create(
            company=freight.company,
            payable_type='TRANSPORTER',
            transporter=freight.vehicle.transporter,
            freight=freight,
            bill_date=timezone.now().date(),
            due_date=due_date,
            total_amount=freight.amount,
            balance_amount=freight.amount,
        )
        logger.info(f"Created payable {payable.id} for freight {freight.id} - {freight.vehicle.transporter.name}")
        
        # Create ledger entry
        freight_account, _ = LedgerAccount.objects.get_or_create(
            company=freight.company,
            code='FREIGHT-EXP',
            defaults={
                'name': 'Freight Expenses',
                'account_type': 'EXPENSE',
            }
        )
        
        creditors_account, _ = LedgerAccount.objects.get_or_create(
            company=freight.company,
            code='CREDITORS',
            defaults={
                'name': 'Sundry Creditors',
                'account_type': 'LIABILITY',
            }
        )
        
        # Freight expense (debit)
        LedgerEntry.objects.create(
            company=freight.company,
            entry_date=payable.bill_date,
            voucher_type='FREIGHT',
            voucher_number=f"FREIGHT-{freight.id}",
            freight=freight,
            account=freight_account,
            debit=freight.amount,
            credit=0,
            narration=f"Freight charges for vehicle {freight.vehicle.vehicle_number} - {freight.vehicle.transporter.name}",
            created_by=user,
        )
        
        # Creditor entry (credit)
        LedgerEntry.objects.create(
            company=freight.company,
            entry_date=payable.bill_date,
            voucher_type='FREIGHT',
            voucher_number=f"FREIGHT-{freight.id}",
            freight=freight,
            account=creditors_account,
            debit=0,
            credit=freight.amount,
            narration=f"Payable to {freight.vehicle.transporter.name} for freight",
            created_by=user,
        )
        
        return payable

    @staticmethod
    @transaction.atomic
    def record_payment(payable, amount, payment_mode, reference_number, user, remarks=''):
        """Record payment to supplier/transporter and update payable."""
        from django.utils import timezone
        
        payment = Payment.objects.create(
            company=payable.company,
            payable=payable,
            payment_date=timezone.now().date(),
            amount=amount,
            payment_mode=payment_mode,
            reference_number=reference_number,
            remarks=remarks,
            created_by=user,
        )
        
        # Create ledger entries
        bank_account, _ = LedgerAccount.objects.get_or_create(
            company=payable.company,
            code='BANK',
            defaults={
                'name': 'Bank Account',
                'account_type': 'ASSET',
            }
        )
        
        creditors_account, _ = LedgerAccount.objects.get_or_create(
            company=payable.company,
            code='CREDITORS',
            defaults={
                'name': 'Sundry Creditors',
                'account_type': 'LIABILITY',
            }
        )
        
        party = payable.party or payable.transporter
        
        # Get the Party model class for isinstance check
        from masters.models import Party
        party_for_ledger = party if isinstance(party, Party) else None
        
        # Creditor entry (debit - reducing creditor)
        LedgerEntry.objects.create(
            company=payable.company,
            entry_date=payment.payment_date,
            voucher_type='PAYMENT',
            voucher_number=reference_number or f"PAY-{payment.id}",
            account=creditors_account,
            party=party_for_ledger,
            debit=amount,
            credit=0,
            narration=f"Payment to {party} - {payable.bill_number or 'Freight'}",
            created_by=user,
        )
        
        # Bank entry (credit)
        LedgerEntry.objects.create(
            company=payable.company,
            entry_date=payment.payment_date,
            voucher_type='PAYMENT',
            voucher_number=reference_number or f"PAY-{payment.id}",
            account=bank_account,
            party=party_for_ledger,
            debit=0,
            credit=amount,
            narration=f"Payment to {party}",
            created_by=user,
        )
        
        # Update payable status after recording payment
        payable.update_status()
        
        return payment

    @staticmethod
    @transaction.atomic
    def record_bill_payment(bill, amount, payment_mode, reference_number, user, remarks=''):
        """Record payment against a transporter bill."""
        from django.utils import timezone
        
        payment = TransporterBillPayment.objects.create(
            transporter_bill=bill,
            payment_date=timezone.now().date(),
            amount=amount,
            payment_mode=payment_mode,
            reference_number=reference_number,
            remarks=remarks,
            created_by=user,
        )
        
        # Create ledger entries for bill payment
        bank_account, _ = LedgerAccount.objects.get_or_create(
            company=bill.company,
            code='BANK',
            defaults={
                'name': 'Bank Account',
                'account_type': 'ASSET',
            }
        )
        
        creditors_account, _ = LedgerAccount.objects.get_or_create(
            company=bill.company,
            code='CREDITORS',
            defaults={
                'name': 'Sundry Creditors',
                'account_type': 'LIABILITY',
            }
        )
        
        # Creditor entry (debit - reducing creditor)
        LedgerEntry.objects.create(
            company=bill.company,
            entry_date=payment.payment_date,
            voucher_type='PAYMENT',
            voucher_number=reference_number or f"BILL-PAY-{payment.id}",
            account=creditors_account,
            debit=amount,
            credit=0,
            narration=f"Payment to {bill.transporter.name} for bill {bill.bill_number}",
            created_by=user,
        )
        
        # Bank entry (credit)
        LedgerEntry.objects.create(
            company=bill.company,
            entry_date=payment.payment_date,
            voucher_type='PAYMENT',
            voucher_number=reference_number or f"BILL-PAY-{payment.id}",
            account=bank_account,
            debit=0,
            credit=amount,
            narration=f"Payment to {bill.transporter.name} for bill {bill.bill_number}",
            created_by=user,
        )
        
        return payment

    @staticmethod
    def get_company_balances(company):
        """Get summary of receivables and payables for a company."""
        receivables = AccountReceivable.objects.filter(company=company)
        payables = AccountPayable.objects.filter(company=company)
        
        return {
            'total_receivable': sum(r.balance_amount for r in receivables),
            'total_payable': sum(p.balance_amount for p in payables),
            'receivable_by_status': {
                'UNPAID': sum(r.balance_amount for r in receivables.filter(status='UNPAID')),
                'PARTIAL': sum(r.balance_amount for r in receivables.filter(status='PARTIAL')),
                'OVERDUE': sum(r.balance_amount for r in receivables.filter(status='OVERDUE')),
            },
            'payable_by_status': {
                'UNPAID': sum(p.balance_amount for p in payables.filter(status='UNPAID')),
                'PARTIAL': sum(p.balance_amount for p in payables.filter(status='PARTIAL')),
                'OVERDUE': sum(p.balance_amount for p in payables.filter(status='OVERDUE')),
            },
        }
