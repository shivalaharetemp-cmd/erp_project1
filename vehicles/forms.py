from django import forms
from .models import Vehicle


class VehicleCreateForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'transporter', 'party', 'loading_point', 'driver_name', 'driver_phone']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'transporter': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.Select(attrs={'class': 'form-control'}),
            'loading_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Loading point'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('company_id', None)  # Remove if passed, but not used
        super().__init__(*args, **kwargs)
        # Show only active transporters and parties (company-neutral)
        self.fields['transporter'].queryset = self.fields['transporter'].queryset.filter(
            is_active=True
        )
        self.fields['party'].queryset = self.fields['party'].queryset.filter(
            is_active=True
        )


class VehicleUpdateForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['transporter', 'party', 'driver_name', 'driver_phone']
        widgets = {
            'transporter': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.Select(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop('company_id', None)  # Remove if passed, but not used
        super().__init__(*args, **kwargs)
        # Show only active transporters and parties (company-neutral)
        self.fields['transporter'].queryset = self.fields['transporter'].queryset.filter(
            is_active=True
        )
        self.fields['party'].queryset = self.fields['party'].queryset.filter(
            is_active=True
        )


class VehicleLoadForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.pop('company_id', None)  # Remove if passed, but not used
        items_count = kwargs.pop('items_count', 1)
        super().__init__(*args, **kwargs)
        from masters.models import Item
        # Show all active items (company-neutral)
        qs = Item.objects.filter(is_active=True)
        for i in range(items_count):
            self.fields[f'item_{i}'] = forms.ModelChoiceField(
                queryset=qs, widget=forms.Select(attrs={'class': 'form-control'}),
                label=f'Item {i+1}'
            )
            self.fields[f'quantity_{i}'] = forms.DecimalField(
                max_digits=15, decimal_places=3,
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Qty in MT'}),
                label=f'Quantity {i+1}'
            )


class VehicleCancelForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for cancellation (min 5 chars)'}),
        min_length=5
    )


class VehicleChangeForm(forms.Form):
    new_vehicle_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New vehicle number'}),
        max_length=20
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for change (min 5 chars)'}),
        min_length=5
    )


class SaleCreateForm(forms.Form):
    """Form to create a sale invoice from a vehicle."""

    def __init__(self, *args, **kwargs):
        vehicle_items = kwargs.pop('vehicle_items', [])
        super().__init__(*args, **kwargs)
        for i, vi in enumerate(vehicle_items):
            self.fields[f'rate_{i}'] = forms.DecimalField(
                label=f'{vi.item.item_name} Rate',
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            )
            self.fields[f'rate_{i}'].vehicle_item_id = str(vi.id)
            self.fields[f'qty_{i}'] = forms.DecimalField(
                label=f'{vi.item.item_name} Qty',
                initial=vi.quantity,
                required=False,
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'readonly': True}),
            )


class CreditNoteCreateForm(forms.Form):
    """Form to create a credit note from a sale."""
    def __init__(self, *args, **kwargs):
        sale_items = kwargs.pop('sale_items', [])
        super().__init__(*args, **kwargs)
        for i, si in enumerate(sale_items):
            self.fields[f'quantity_{i}'] = forms.DecimalField(
                label=f'{si.item.item_name} Qty (max: {si.quantity})',
                initial=si.quantity,
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            )
            self.fields[f'quantity_{i}'].sale_item_id = str(si.id)
            self.fields[f'rate_{i}'] = forms.DecimalField(
                label=f'{si.item.item_name} Rate',
                initial=si.rate,
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            )
            self.fields[f'rate_{i}'].sale_item_id = str(si.id)

