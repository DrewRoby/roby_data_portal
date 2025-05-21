# inventory/forms.py
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Warehouse, Rack, Shelf, Bin, Item, Disposition, StockAddition

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RackForm(forms.ModelForm):
    class Meta:
        model = Rack
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ShelfForm(forms.ModelForm):
    class Meta:
        model = Shelf
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BinForm(forms.ModelForm):
    class Meta:
        model = Bin
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'description', 'quantity', 'sku']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ItemTransferForm(forms.Form):
    warehouse = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_warehouse'})
    )
    rack = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_rack'})
    )
    shelf = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_shelf'})
    )
    bin = forms.ChoiceField(
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_bin'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantity'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Populate warehouse choices
            warehouses = Warehouse.objects.filter(user=user)
            self.fields['warehouse'].choices = [(w.id, w.name) for w in warehouses]
            
            # Default choices for other fields (will be updated via AJAX)
            self.fields['rack'].choices = [('', 'Select Rack')]
            self.fields['shelf'].choices = [('', 'Select Shelf')]
            self.fields['bin'].choices = [('', 'Select Bin')]

class RestockForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'restock-quantity'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'id': 'restock-notes', 'rows': 2})
    )

class SearchForm(forms.Form):
    query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter name, description, SKU...'
        })
    )
    type = forms.ChoiceField(
        choices=[
            ('all', 'All Categories'),
            ('warehouse', 'Warehouses'),
            ('rack', 'Racks'),
            ('shelf', 'Shelves'),
            ('bin', 'Bins'),
            ('item', 'Items'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class DispositionForm(forms.ModelForm):
    class Meta:
        model = Disposition
        fields = ['quantity', 'disposition_type', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'disposition_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item', None)
        super().__init__(*args, **kwargs)
        if self.item:
            self.fields['quantity'].widget.attrs['max'] = self.item.quantity
            self.fields['quantity'].help_text = f'Maximum available: {self.item.quantity}'
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if self.item and quantity > self.item.quantity:
            raise ValidationError(f'Cannot dispose more than the available quantity ({self.item.quantity}).')
        return quantity

class StockAdditionForm(forms.ModelForm):
    class Meta:
        model = StockAddition
        fields = ['quantity', 'addition_type', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'addition_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }