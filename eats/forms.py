from django import forms
from django.forms import ModelForm
from eats.models import *


class NewBusinessForm(ModelForm):
    class Meta:
        model = Business
        exclude = ["description", "latitude", "longitude"]
        widgets = {"open_date": forms.DateInput(attrs={"type": "date"}),
                   "close_date": forms.DateInput(attrs={"type": "date"})}


class EditBusinessForm(ModelForm):
    class Meta:
        model = Business
        exclude = ["description", "latitude", "longitude"]
        widgets = {"open_date": forms.DateInput(attrs={"type": "date"}),
                   "close_date": forms.DateInput(attrs={"type": "date"})}


class NewVendorForm(ModelForm):
    class Meta:
        model = Vendor
        exclude = ["description"]
        widgets = {"open_date": forms.DateInput(attrs={"type": "date"}),
                   "close_date": forms.DateInput(attrs={"type": "date"})}


class EditVendorForm(ModelForm):
    class Meta:
        model = Vendor
        exclude = ["description"]
        widgets = {"open_date": forms.DateInput(attrs={"type": "date"}),
                   "close_date": forms.DateInput(attrs={"type": "date"})}


class NewTipForm(ModelForm):
    class Meta:
        model = Tip
        exclude = ["open_date"]


class EditTipForm(ModelForm):
    class Meta:
        model = Tip
        fields = "__all__"
        widgets = {"open_date": forms.DateInput(attrs={"type": "date"})}


class CreateRefLinkForm(ModelForm):
    class Meta:
        model = ReferenceLink
        fields = "__all__"
        widgets = {"date_published": forms.DateInput(attrs={"type": "date"})}
