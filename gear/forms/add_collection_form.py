from django import forms
from gear.forms.base_form import BaseForm
from gear.models import Item
from users.models import UserProfile
from users.service.service_instances import _patron_service
from gear.views.base import is_librarian


class CollectionForm(BaseForm):
    image = forms.ImageField(required=False)

    is_private = forms.BooleanField(
        required=False,
        label="Private Collection",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-6 h-6 border-2 border-gray-300 focus:ring-2 focus:ring-primary focus:outline-none duration-200 ease-in-out checked:bg-primary checked:border-transparent shadow-sm"
            }
        ),
    )

    allowed_users = forms.ModelMultipleChoiceField(
        queryset=UserProfile.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    items = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.request_user:
            self.fields[
                "allowed_users"
            ].queryset = _patron_service.get_all_patrons().exclude(
                email=self.request_user.email
            )

        self.fields["items"].queryset = Item.objects.all()

        if not is_librarian(self.request_user):
            self.fields["items"].queryset = (
                self.fields["items"]
                .queryset.filter(collections__is_private=False)
                .distinct()
            )
