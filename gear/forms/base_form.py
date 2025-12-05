from django import forms


class BaseForm(forms.Form):
    title = forms.CharField(
        max_length=50,
        required=True,
        error_messages={"required": "Please enter a Title."},
        widget=forms.TextInput(
            attrs={
                "placeholder": "Title",
                "class": "w-full px-4 h-12 rounded-lg border-1 border-gray-300 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary",
            }
        ),
    )
    description = forms.CharField(
        max_length=500,
        required=True,
        error_messages={"required": "Please enter a Description."},
        widget=forms.Textarea(
            attrs={
                "placeholder": "Description",
                "class": "w-full px-4 rounded-lg border-1 border-gray-300 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary h-[6rem] max-h-[12rem] resize-y",
                "rows": 4,
                "style": "padding-top: 8px; resize: none;",
            }
        ),
    )
