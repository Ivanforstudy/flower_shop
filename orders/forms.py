from django import forms

class OrderCreateForm(forms.Form):
    address = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=20)
