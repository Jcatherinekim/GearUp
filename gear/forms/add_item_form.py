from django import forms

from gear.forms.base_form import BaseForm


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [super(MultipleFileField, self).clean(f, initial) for f in data]
        return [super(MultipleFileField, self).clean(data, initial)]


class ItemForm(BaseForm):
    LOCATION_CHOICE = [
        ("", "Location..."),
        ("in_store", "In Store"),
        ("online", "Online"),
    ]
    location = forms.ChoiceField(
        choices=LOCATION_CHOICE,
        required=True,
        error_messages={"required": "Please select a location."},
        widget=forms.Select(
            attrs={
                "class": "w-25 h-12 pr-3 text-left rounded-lg border-1 border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            }
        ),
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=9999,
        required=True,
        error_messages={
            "required": "Please enter a quantity.",
            "min_value": "Quantity must be at least 1.",
            "max_value": "Quantity cannot be larger than 9999. Please enter a smaller number.",
        },
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Quantity",
                "class": "w-full h-12 pr-3 text-left rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
            }
        ),
    )
    images = MultipleFileField(
        required=False, help_text="You can upload multiple images."
    )
