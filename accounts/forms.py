from django import forms
from .models import Customer, MilkEntry
from .models import Customer, MilkEntry, Payment, PRICE_PER_LITRE

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'balance_amount']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer name'
            }),
            'balance_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter balance amount',
                'step': '0.01',
                'min': '0'
            }),
        }

class MilkEntryForm(forms.ModelForm):
    # extra field to allow typing a new customer name
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type new customer name (or leave blank to select)',
            'id': 'new_customer_input'
        }),
        label='New Customer (optional)'
    )

    class Meta:
        model = MilkEntry
        fields = ['customer', 'customer_name', 'date', 'quantity_ml']
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select select-customer',
                'id': 'id_customer_select',
                'data-placeholder': '-- Select or search customer --'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_date_input'
            }),
            'quantity_ml': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
                'placeholder': 'Enter quantity in ml (0 allowed)',
                'id': 'id_quantity_input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by('name') # type: ignore
        self.fields['customer'].required = False

    def clean(self):
        cleaned = super().clean()
        cust = cleaned.get('customer')
        cust_name = cleaned.get('customer_name')
        qty = cleaned.get('quantity_ml')
        
        if not cust and not cust_name:
            raise forms.ValidationError("Please select an existing customer or enter a customer name.")
        
        # Allow 0 quantity
        if qty is None:
            raise forms.ValidationError("Quantity is required.")
        
        return cleaned
    
    # =========================================================
# ADD THIS TO YOUR forms.py
# =========================================================
# Make sure these imports are at the top of forms.py:
#   from django import forms
#   from .models import Payment

class PaymentForm(forms.ModelForm):
    class Meta:
        model  = Payment
        fields = ['amount', 'paid_on', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount (₹)',
                'min': '1',
                'step': '0.01',
            }),
            'paid_on': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'note': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional note (e.g. cash, UPI)',
            }),
        }