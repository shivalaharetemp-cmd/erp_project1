#!/usr/bin/env python
"""Debug script to check why payables aren't being created."""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from freight.models import Freight
from accounts.models import AccountPayable

print("=" * 60)
print("DEBUGGING PAYABLES ISSUE")
print("=" * 60)

# Count freights and payables
freight_count = Freight.objects.count()
payable_count = AccountPayable.objects.count()

print(f"\nTotal Freights: {freight_count}")
print(f"Total Payables: {payable_count}")

if freight_count > 0:
    print("\n--- Checking last 5 freights ---")
    for f in Freight.objects.order_by('-created_at')[:5]:
        print(f"\nFreight: {f.id}")
        print(f"  Vehicle: {f.vehicle.vehicle_number}")
        print(f"  Transporter: {f.vehicle.transporter}")
        print(f"  Amount: {f.amount}")
        print(f"  Company: {f.company}")
        
        # Check if payable exists
        payable = AccountPayable.objects.filter(freight=f).first()
        if payable:
            print(f"  Payable: YES - {payable.id} - {payable.status}")
        else:
            print(f"  Payable: NO - attempting to create...")
            try:
                from accounts.services import AccountingService
                from core.models import User
                # Get first superuser as creator
                user = User.objects.filter(is_superuser=True).first()
                if user:
                    new_payable = AccountingService.create_payable_for_freight(f, user)
                    print(f"  Payable CREATED: {new_payable.id}")
                else:
                    print("  ERROR: No user found to create payable")
            except ValueError as e:
                print(f"  ERROR (ValueError): {e}")
            except Exception as e:
                print(f"  ERROR ({type(e).__name__}): {e}")
                import traceback
                traceback.print_exc()

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
