from django import forms
from gear.forms.base_form import BaseForm
from gear.models import Collection, Item
from users.models import UserProfile
from gear.service.service_instances import _item_service, _collection_service
from django.db.models import Q


class LibraryForm(BaseForm):
    image = forms.ImageField(required=False)

    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    collections = forms.ModelMultipleChoiceField(
        queryset=Collection.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user", None)
        item_search_query = kwargs.pop("item_search_query", "")
        collection_search_query = kwargs.pop("collection_search_query", "")
        super().__init__(*args, **kwargs)

        items_qs = _item_service.get_all_items()
        collections_qs = _collection_service.get_all_collections()

        if item_search_query:
            items_qs = items_qs.filter(
                Q(title__icontains=item_search_query)
                | Q(description__icontains=item_search_query)
            )

        if collection_search_query:
            collections_qs = collections_qs.filter(
                Q(title__icontains=collection_search_query)
                | Q(description__icontains=collection_search_query)
            )

        self.fields["items"].queryset = items_qs
        self.fields["collections"].queryset = collections_qs
