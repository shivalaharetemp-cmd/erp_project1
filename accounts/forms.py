from django import forms


class ReceiptForm(forms.Form):
    """Form for recording receipts from customers."""
    amount = forms.DecimalField(
        max_digits=15, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Amount'
    )
    payment_mode = forms.ChoiceField(
        choices=[
            ('CASH', 'Cash'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CHEQUE', 'Cheque'),
            ('UPI', 'UPI'),
            ('NEFT', 'NEFT/RTGS'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Mode'
    )
    reference_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cheque/Transaction Number'}),
        label='Reference Number'
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks'}),
        label='Remarks'
    )


class PaymentForm(forms.Form):
    """Form for recording payments to suppliers."""
    amount = forms.DecimalField(
        max_digits=15, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Amount'
    )
    payment_mode = forms.ChoiceField(
        choices=[
            ('CASH', 'Cash'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CHEQUE', 'Cheque'),
            ('UPI', 'UPI'),
            ('NEFT', 'NEFT/RTGS'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Mode'
    )
    reference_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cheque/Transaction Number'}),
        label='Reference Number'
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks'}),
        label='Remarks'
    )


class TransporterBillPaymentForm(forms.Form):
    """Form for recording payments against transporter bills."""
    amount = forms.DecimalField(
        max_digits=15, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Amount'
    )
    payment_mode = forms.ChoiceField(
        choices=[
            ('CASH', 'Cash'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CHEQUE', 'Cheque'),
            ('UPI', 'UPI'),
            ('NEFT', 'NEFT/RTGS'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Mode'
    )
    reference_number = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cheque/Transaction Number'}),
        label='Reference Number'
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional remarks'}),
        label='Remarks'
    )
