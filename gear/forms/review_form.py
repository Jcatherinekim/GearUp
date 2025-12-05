from django import forms
from gear.models import ItemReview


class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.HiddenInput(attrs={"class": "focus:ring"}),
        required=True,
    )
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 3, "class": "textarea textarea-bordered w-full"}
        ),
        required=False,
    )

    class Meta:
        model = ItemReview
        fields = ["rating", "comment"]
