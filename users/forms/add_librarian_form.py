
from django import forms
from users.models import UserProfile
from users.service.service_instances import _patron_service


class AddLibrarianForm(forms.Form):
    new_librarians = forms.ModelMultipleChoiceField(
        queryset=UserProfile.objects.none(),
        required=True,
        error_messages={'required': 'Please select a librarian.'},
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.request_user:
            patrons = _patron_service.get_all_patrons().exclude(email=self.request_user.email)
            self.fields["new_librarians"].queryset = patrons
