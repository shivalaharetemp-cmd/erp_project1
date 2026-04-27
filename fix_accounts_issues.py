#!/usr/bin/env python
"""
Fix script for accounts app issues with transporter bills and payables.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import transaction
from accounts.models import AccountPayable, Payment, TransporterBill, TransporterBillPayment
from accounts.services import AccountingService

def fix_payable_status():
    """Fix payable status for all records that need updating."""
    print("Fixing payable statuses...")
    
    # Find payables where status doesn't match the actual payment situation
    payables = AccountPayable.objects.all()
    fixed = 0
    
    for payable in payables:
        old_status = payable.status
        
        # Recalculate paid amount from payments
        total_paid = sum(p.amount for p in payable.payments.all())
        if total_paid != payable.paid_amount:
            payable.paid_amount = total_paid
            print(f"  Fixed paid_amount for {payable.id}: was {payable.paid_amount}, now {total_paid}")
        
        # Call update_status to set correct status
        payable.update_status()
        
        if payable.status != old_status:
            print(f"  Updated {payable.id}: {old_status} -> {payable.status}")
            fixed += 1
    
    print(f"Fixed {fixed} payable records")
    return fixed


def fix_transporter_bill_status():
    """Fix transporter bill status."""
    print("\nFixing transporter bill statuses...")
    
    bills = TransporterBill.objects.all()
    fixed = 0
    
    for bill in bills:
        old_status = bill.status
        
        # Recalculate paid amount
        total_paid = sum(bp.amount for bp in bill.bill_payments.all())
        if total_paid != bill.paid_amount:
            bill.paid_amount = total_paid
            print(f"  Fixed paid_amount for bill {bill.id}: was {bill.paid_amount}, now {total_paid}")
        
        # Calculate and update
        bill.calculate_total()
        bill.update_status()
        
        if bill.status != old_status:
            print(f"  Updated bill {bill.id}: {old_status} -> {bill.status}")
            fixed += 1
    
    print(f"Fixed {fixed} transporter bill records")
    return fixed


def verify_fixes():
    """Verify the fixes are working."""
    print("\n=== VERIFICATION ===")
    
    # Check payables
    unpaid_count = AccountPayable.objects.filter(status='UNPAID').count()
    partial_count = AccountPayable.objects.filter(status='PARTIAL').count()
    paid_count = AccountPayable.objects.filter(status='PAID').count()
    overdue_count = AccountPayable.objects.filter(status='OVERDUE').count()
    
    print(f"\nPayables Status:")
    print(f"  UNPAID: {unpaid_count}")
    print(f"  PARTIAL: {partial_count}")
    print(f"  PAID: {paid_count}")
    print(f"  OVERDUE: {overdue_count}")
    print(f"  TOTAL: {unpaid_count + partial_count + paid_count + overdue_count}")
    
    # Check transporter bills
    draft_count = TransporterBill.objects.filter(status='DRAFT').count()
    approved_count = TransporterBill.objects.filter(status='APPROVED').count()
    partial_bill_count = TransporterBill.objects.filter(status='PARTIAL').count()
    paid_bill_count = TransporterBill.objects.filter(status='PAID').count()
    
    print(f"\nTransporter Bills Status:")
    print(f"  DRAFT: {draft_count}")
    print(f"  APPROVED: {approved_count}")
    print(f"  PARTIAL: {partial_bill_count}")
    print(f"  PAID: {paid_bill_count}")
    print(f"  TOTAL: {draft_count + approved_count + partial_bill_count + paid_bill_count}")


if __name__ == '__main__':
    print("=" * 60)
    print("ACCOUNTS APP FIX SCRIPT")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            fix_payable_status()
            fix_transporter_bill_status()
            verify_fixes()
        
        print("\n" + "=" * 60)
        print("FIXES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
