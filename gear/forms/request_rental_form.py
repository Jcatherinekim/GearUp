from django import forms


class Request_Rental_Form(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        required=True,
        error_messages={"required": "Please enter a quantity."},
        widget=forms.NumberInput(
            attrs={
                "placeholder": "Rental Quantity",
                "class": "w-25 h-12 pr-3 text-left rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent",
            }
        ),
    )
