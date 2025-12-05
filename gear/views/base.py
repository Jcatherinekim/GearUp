from users.service.service_instances import _librarian_service, _patron_service
from django.shortcuts import render
from ..models import Collection


def is_librarian(user):
    return _librarian_service.is_librarian(user)


def is_patron(user):
    return _patron_service.is_patron(user)


def collection_detail(request, collection_id):
    collection = Collection.objects.get(id=collection_id)
    if collection.created_by and is_patron(collection.created_by.userprofile):
        creator_text = f"Created by {collection.created_by.userprofile.name}"
    else:
        creator_text = "Created by GearUp"

    context = {
        "collection": collection,
        "creator_text": creator_text,
    }
    return render(request, "your_template.html", context)
