from django import forms
from .models import Party, Item, Transporter, PurchaseOrder, PurchaseOrderItem, Unit, State, Country, Address


# Address Form for inline use
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['address_line_1', 'address_line_2', 'landmark', 'city', 'district', 'pincode', 'state', 'country']
        widgets = {
            'address_line_1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_2': forms.TextInput(attrs={'class': 'form-control'}),
            'landmark': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.Select(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
        }


class PartyForm(forms.ModelForm):
    # Address fields inline
    address_line_1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Address Line 1')
    address_line_2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Address Line 2')
    landmark = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    district = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.ModelChoiceField(queryset=State.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}))
    country = forms.ModelChoiceField(queryset=Country.objects.filter(is_active=True), initial=1, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Party
        fields = ['party_code', 'party_name', 'gstin', 'phone', 'email', 'party_type', 'credit_limit', 'payment_terms']
        widgets = {
            'party_code': forms.TextInput(attrs={'class': 'form-control'}),
            'party_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 15}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'party_type': forms.Select(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk and instance.address:
            # Pre-populate address fields
            self.fields['address_line_1'].initial = instance.address.address_line_1
            self.fields['address_line_2'].initial = instance.address.address_line_2
            self.fields['landmark'].initial = instance.address.landmark
            self.fields['city'].initial = instance.address.city
            self.fields['district'].initial = instance.address.district
            self.fields['pincode'].initial = instance.address.pincode
            self.fields['state'].initial = instance.address.state
            self.fields['country'].initial = instance.address.country

    def save(self, commit=True):
        # Save address first
        address_data = {
            'address_line_1': self.cleaned_data.pop('address_line_1'),
            'address_line_2': self.cleaned_data.pop('address_line_2', ''),
            'landmark': self.cleaned_data.pop('landmark', ''),
            'city': self.cleaned_data.pop('city'),
            'district': self.cleaned_data.pop('district', ''),
            'pincode': self.cleaned_data.pop('pincode'),
            'state': self.cleaned_data.pop('state'),
            'country': self.cleaned_data.pop('country'),
        }

        instance = super().save(commit=False)

        if instance.pk and instance.address:
            # Update existing address
            for key, value in address_data.items():
                setattr(instance.address, key, value)
            if commit:
                instance.address.save()
        else:
            # Create new address
            address = Address.objects.create(**address_data)
            instance.address = address

        if commit:
            instance.save()

        return instance


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['item_code', 'item_name', 'unit', 'tax_rate', 'hsn_code']
        widgets = {
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'hsn_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['unit'].queryset = Unit.objects.filter(is_active=True)


class TransporterForm(forms.ModelForm):
    # Address fields inline
    address_line_1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Address Line 1')
    address_line_2 = forms.CharField(max_length=255, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), label='Address Line 2')
    landmark = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    district = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(max_length=10, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.ModelChoiceField(queryset=State.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'form-control'}))
    country = forms.ModelChoiceField(queryset=Country.objects.filter(is_active=True), initial=1, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Transporter
        fields = ['name', 'gstin', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gstin': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 15}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = self.instance
        if instance and instance.pk and instance.address:
            # Pre-populate address fields
            self.fields['address_line_1'].initial = instance.address.address_line_1
            self.fields['address_line_2'].initial = instance.address.address_line_2
            self.fields['landmark'].initial = instance.address.landmark
            self.fields['city'].initial = instance.address.city
            self.fields['district'].initial = instance.address.district
            self.fields['pincode'].initial = instance.address.pincode
            self.fields['state'].initial = instance.address.state
            self.fields['country'].initial = instance.address.country

    def save(self, commit=True):
        # Save address first
        address_data = {
            'address_line_1': self.cleaned_data.pop('address_line_1'),
            'address_line_2': self.cleaned_data.pop('address_line_2', ''),
            'landmark': self.cleaned_data.pop('landmark', ''),
            'city': self.cleaned_data.pop('city'),
            'district': self.cleaned_data.pop('district', ''),
            'pincode': self.cleaned_data.pop('pincode'),
            'state': self.cleaned_data.pop('state'),
            'country': self.cleaned_data.pop('country'),
        }

        instance = super().save(commit=False)

        if instance.pk and instance.address:
            # Update existing address
            for key, value in address_data.items():
                setattr(instance.address, key, value)
            if commit:
                instance.address.save()
        else:
            # Create new address
            address = Address.objects.create(**address_data)
            instance.address = address

        if commit:
            instance.save()

        return instance


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['code', 'name', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 10}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StateForm(forms.ModelForm):
    class Meta:
        model = State
        fields = ['name', 'code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CountryForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = ['name', 'code', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
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
