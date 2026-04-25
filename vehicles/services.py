from django.db import transaction
from django.utils import timezone
from audit.services import AuditService


class VehicleService:
    """Service for vehicle workflow operations."""

    @staticmethod
    @transaction.atomic
    def create_vehicle(data, user, company_id=None, company=None, request=None):
        """Create a new vehicle placement (company-neutral - assigned at sale time)."""
        from .models import Vehicle
        from core.models import Company as CompanyModel
        
        # Don't set company here - it will be assigned when creating sale invoice
        vehicle = Vehicle.objects.create(
            created_by=user,
            **data
        )

        if request:
            # Get company from request context for audit, even though vehicle.company is None
            cid = request.session.get('company_id') if hasattr(request, 'session') else None
            audit_company = None
            if cid:
                try:
                    audit_company = CompanyModel.objects.get(id=cid)
                except CompanyModel.DoesNotExist:
                    pass
            
            AuditService.log(
                user=user, company=audit_company,
                action='CREATE', model_name='Vehicle',
                object_id=str(vehicle.id),
                new_value={'vehicle_number': vehicle.vehicle_number},
                request=request,
            )
        return vehicle

    @staticmethod
    @transaction.atomic
    def load_vehicle(vehicle, items_data, user, request=None):
        """Load items onto a vehicle. Locks quantity and vehicle number."""
        if vehicle.status != 'Pending':
            raise ValueError(f"Cannot load vehicle with status: {vehicle.status}")

        from .models import VehicleItem
        from masters.models import Item

        created_items = []
        for item_data in items_data:
            item_id = item_data['item_id']
            quantity = item_data['quantity']

            try:
                # Don't filter by company - vehicles are company-neutral at load time
                item = Item.objects.get(id=item_id, is_active=True)
            except Item.DoesNotExist:
                raise ValueError(f"Item {item_id} not found or inactive.")

            v_item = VehicleItem.objects.create(
                vehicle=vehicle,
                item=item,
                quantity=quantity,
            )
            created_items.append(v_item)

        vehicle.status = 'Loaded'
        vehicle.loaded_at = timezone.now()
        vehicle.version += 1
        vehicle.save()

        if request:
            # Get company from request session for audit (vehicle.company is still None)
            from core.models import Company as CompanyModel
            audit_company = None
            cid = request.session.get('company_id') if hasattr(request, 'session') else None
            if cid:
                try:
                    audit_company = CompanyModel.objects.get(id=cid)
                except CompanyModel.DoesNotExist:
                    pass
            
            AuditService.log(
                user=user, company=audit_company,
                action='LOAD', model_name='Vehicle',
                object_id=str(vehicle.id),
                new_value={
                    'vehicle_number': vehicle.vehicle_number,
                    'items': [{'item': str(vi.item.item_name), 'qty': str(vi.quantity)} for vi in created_items]
                },
                request=request,
            )
        return vehicle

    @staticmethod
    @transaction.atomic
    def cancel_vehicle(vehicle, reason, user, request=None):
        """Cancel a vehicle. Handles sales reversal if needed."""
        if vehicle.status == 'Cancelled':
            raise ValueError("Vehicle is already cancelled.")

        # Get company for audit logging (vehicle.company might be None for company-neutral vehicles)
        company = vehicle.company
        if company is None and request:
            from core.models import Company as CompanyModel
            cid = request.session.get('company_id') if hasattr(request, 'session') else None
            if cid:
                try:
                    company = CompanyModel.objects.get(id=cid)
                except CompanyModel.DoesNotExist:
                    pass
        
        old_status = vehicle.status

        vehicle.status = 'Cancelled'
        vehicle.cancelled_at = timezone.now()
        vehicle.cancellation_reason = reason
        vehicle.cancelled_by = user
        vehicle.version += 1
        vehicle.save()

        if request:
            AuditService.log(
                user=user, company=company,
                action='CANCEL', model_name='Vehicle',
                object_id=str(vehicle.id),
                old_value={'status': old_status},
                new_value={'status': 'Cancelled'},
                reason=reason,
                request=request,
            )

        return vehicle

    @staticmethod
    @transaction.atomic
    def change_vehicle(vehicle, new_number, reason, user, request=None):
        """Change vehicle number with permission check and audit."""
        if vehicle.status not in ('Pending', 'Loaded'):
            raise ValueError(f"Cannot change vehicle number for status: {vehicle.status}")

        old_number = vehicle.vehicle_number

        from .models import VehicleChangeLog
        VehicleChangeLog.objects.create(
            vehicle=vehicle,
            old_vehicle_number=old_number,
            new_vehicle_number=new_number,
            changed_by=user,
            reason=reason,
        )

        vehicle.vehicle_number = new_number
        vehicle.version += 1
        vehicle.save()

        if request:
            # Get company for audit logging (vehicle.company might be None for company-neutral vehicles)
            company = vehicle.company
            if company is None:
                from core.models import Company as CompanyModel
                cid = request.session.get('company_id') if hasattr(request, 'session') else None
                if cid:
                    try:
                        company = CompanyModel.objects.get(id=cid)
                    except CompanyModel.DoesNotExist:
                        pass
            
            AuditService.log(
                user=user, company=company,
                action='CHANGE_VEHICLE', model_name='Vehicle',
                object_id=str(vehicle.id),
                old_value={'vehicle_number': old_number},
                new_value={'vehicle_number': new_number},
                reason=reason,
                request=request,
            )

        return vehicle

    @staticmethod
    def get_po_rate(party, item, company):
        """Fetch rate from active purchase order if available."""
        from masters.models import PurchaseOrder, PurchaseOrderItem
        from django.utils import timezone

        po_item = PurchaseOrderItem.objects.filter(
            purchase_order__party=party,
            purchase_order__company=company,
            purchase_order__status__in=['Confirmed', 'Partially Fulfilled'],
            purchase_order__valid_until__gte=timezone.now().date(),
            item=item,
        ).first()

        if po_item:
            return po_item.rate, po_item.purchase_order.po_number
        return None, None

    @staticmethod
    def get_all_po_options(party, item, company):
        """Fetch all active purchase orders for a party+item combo."""
        from masters.models import PurchaseOrder, PurchaseOrderItem
        from django.utils import timezone

        po_items = PurchaseOrderItem.objects.filter(
            purchase_order__party=party,
            purchase_order__company=company,
            purchase_order__status__in=['Confirmed', 'Partially Fulfilled'],
            purchase_order__valid_until__gte=timezone.now().date(),
            item=item,
        ).select_related('purchase_order').order_by('-purchase_order__po_date')

        options = []
        for po_item in po_items:
            options.append({
                'po_id': str(po_item.purchase_order.id),
                'po_number': po_item.purchase_order.po_number,
                'rate': float(po_item.rate),
                'po_date': po_item.purchase_order.po_date,
            })
        return options

    @staticmethod
    @transaction.atomic
    def dispatch_vehicle(vehicle, user, request=None):
        """Mark vehicle as dispatched (InTransit)."""
        if vehicle.status != 'Loaded':
            raise ValueError(f"Cannot dispatch vehicle with status: {vehicle.status}")
        
        vehicle.status = 'InTransit'
        vehicle.dispatched_at = timezone.now()
        vehicle.version += 1
        vehicle.save()

        if request:
            company = vehicle.company
            AuditService.log(
                user=user, company=company,
                action='DISPATCH', model_name='Vehicle',
                object_id=str(vehicle.id),
                new_value={'vehicle_number': vehicle.vehicle_number, 'status': 'InTransit'},
                request=request,
            )
        return vehicle

    @staticmethod
    @transaction.atomic
    def deliver_vehicle(vehicle, delivered_to='', pod_reference='', delivery_remarks='', user=None, request=None):
        """Mark vehicle as delivered with POD details."""
        if vehicle.status not in ('InTransit', 'Loaded'):
            raise ValueError(f"Cannot mark as delivered from status: {vehicle.status}")
        
        vehicle.status = 'Delivered'
        vehicle.delivered_at = timezone.now()
        vehicle.delivered_to = delivered_to
        vehicle.pod_reference = pod_reference
        vehicle.delivery_remarks = delivery_remarks
        vehicle.version += 1
        vehicle.save()

        if request and user:
            company = vehicle.company
            AuditService.log(
                user=user, company=company,
                action='DELIVER', model_name='Vehicle',
                object_id=str(vehicle.id),
                new_value={
                    'vehicle_number': vehicle.vehicle_number,
                    'status': 'Delivered',
                    'delivered_to': delivered_to,
                    'pod_reference': pod_reference
                },
                request=request,
            )
        return vehicle
