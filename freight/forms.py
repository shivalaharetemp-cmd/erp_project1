from django import forms
from .models import Freight, ReturnFreight


class FreightForm(forms.ModelForm):
    class Meta:
        model = Freight
        fields = ['freight_type', 'quantity', 'rate', 'amount']
        widgets = {
            'freight_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        freight_type = cleaned_data.get('freight_type')
        quantity = cleaned_data.get('quantity')
        rate = cleaned_data.get('rate')
        amount = cleaned_data.get('amount')
        
        if freight_type in ['PerQuantity', 'Guaranteed']:
            if not rate:
                raise forms.ValidationError('Rate is required for PerQuantity and Guaranteed types.')
        elif freight_type == 'Fixed':
            if not amount:
                raise forms.ValidationError('Amount is required for Fixed type.')
        
        return cleaned_data


class ReturnFreightForm(forms.ModelForm):
    class Meta:
        model = ReturnFreight
        fields = ['credit_note', 'freight_type', 'quantity', 'rate', 'amount']
        widgets = {
            'credit_note': forms.Select(attrs={'class': 'form-control'}),
            'freight_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        company_id = kwargs.pop('company_id', None)
        super().__init__(*args, **kwargs)
        if company_id:
            self.fields['credit_note'].queryset = self.fields['credit_note'].queryset.filter(
                company_id=company_id, status='Active'
            )

