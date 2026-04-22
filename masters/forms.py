from django import forms
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem


class PartyForm(forms.ModelForm):
    class Meta:
        model = Party
        fields = ['company', 'party_code', 'party_name', 'gstin', 'state', 'state_code', 'address',
                  'phone', 'email', 'party_type', 'credit_limit', 'payment_terms']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'party_code': forms.TextInput(attrs={'class': 'form-control'}),
            'party_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 15}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'state_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'party_type': forms.Select(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['company', 'item_code', 'item_name', 'unit', 'tax_rate', 'hsn_code']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
        }


class TransporterForm(forms.ModelForm):
    class Meta:
        model = Transporter
        fields = ['company', 'name', 'gstin', 'phone', 'address']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 15}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'quantity', 'rate']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder, PurchaseOrderItem,
    form=PurchaseOrderItemForm, extra=1, can_delete=True
)


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['company', 'party', 'po_number', 'po_date', 'valid_until', 'status']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.Select(attrs={'class': 'form-control'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'po_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
