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

    def __init__(self, *args, **kwargs):
        vehicle_items = kwargs.pop('vehicle_items', [])
        companies = kwargs.pop('companies', None)
        super().__init__(*args, **kwargs)
        
        if companies is not None:
            self.fields['company'].queryset = companies
        
        # Add rate fields for each vehicle item
        for i, vi in enumerate(vehicle_items):
            self.fields[f'rate_{i}'] = forms.DecimalField(
                label=f'{vi.item.item_name} Rate',
                widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            )
            self.fields[f'rate_{i}'].vehicle_item_id = str(vi.id)
            self.fields[f'qty_{i}'] = forms.DecimalField(
                label=f'{vi.item.item_name} Qty',
                initial=vi.quantity,
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
