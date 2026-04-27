from django import forms


class SaleCreateForm(forms.Form):
    """Form to create a sale invoice from a vehicle."""
    vehicle_id = forms.UUIDField(widget=forms.HiddenInput())
    company = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Company for Invoice',
        help_text='Select the company that will issue this invoice'
    )
    loading_point = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Loading Point',
        required=False
    )

    def __init__(self, *args, **kwargs):
        vehicle_items = kwargs.pop('vehicle_items', [])
        companies = kwargs.pop('companies', None)
        loading_points = kwargs.pop('loading_points', None)
        super().__init__(*args, **kwargs)

        if companies is not None:
            self.fields['company'].queryset = companies

        if loading_points is not None:
            self.fields['loading_point'].queryset = loading_points

        # Add selectable item fields with quantity input
        for i, vi in enumerate(vehicle_items):
            remaining = vi.remaining_quantity

            # Checkbox to include this item
            self.fields[f'include_{i}'] = forms.BooleanField(
                label=f'{vi.item.item_name} (Loaded: {vi.quantity}, Remaining: {remaining})',
                required=False,
                initial=remaining > 0,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            )
            self.fields[f'include_{i}'].vehicle_item_id = str(vi.id)
            self.fields[f'include_{i}'].remaining_qty = float(remaining)

            # Editable quantity (max = remaining)
            self.fields[f'qty_{i}'] = forms.DecimalField(
                label='Quantity',
                initial=min(remaining, vi.quantity) if remaining > 0 else 0,
                min_value=0.001,
                max_value=remaining,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.001',
                    'max': float(remaining),
                }),
                required=False,
            )

            # Rate field
            self.fields[f'rate_{i}'] = forms.DecimalField(
                label='Rate',
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
                required=False,
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
