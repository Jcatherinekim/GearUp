from django.shortcuts import render, get_object_or_404
from users.service.service_instances import _librarian_service, _patron_service
from gear.models import Collection
from django.shortcuts import redirect
from gear.forms.add_collection_form import CollectionForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from gear.models import CollectionItem


def is_librarian(user):
    return _librarian_service.is_librarian(user)


def is_patron(user):
    return _patron_service.is_patron(user)


def collection_detail(request, collection_id):
    collection = get_object_or_404(
        Collection.objects.prefetch_related("items__collections"), id=collection_id
    )
    if collection.is_private and not request.user.is_authenticated:
        return redirect("gear:home")

    user = request.user

    creator_text = (
        f"Created by {collection.created_by}" if collection.created_by else ""
    )

    user_is_librarian = user.is_authenticated and is_librarian(user)
    user_is_creator = user.is_authenticated and (user == collection.created_by)
    user_has_access = False

    if user.is_authenticated and hasattr(user, "userprofile"):
        user_has_access = collection.allowed_users.filter(
            id=user.userprofile.id
        ).exists()

    context = {
        "collection": collection,
        "creator_text": creator_text,
        "user_is_librarian": user_is_librarian,
        "user_is_creator": user_is_creator,
        "user_has_access": user_has_access,
    }
    return render(request, "detail/collection_detail.html", context)


@user_passes_test(is_librarian, login_url="gear:home")
def edit_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.method == "POST":
        form = CollectionForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            items = form.cleaned_data["items"]
            collection.title = form.cleaned_data["title"]
            collection.description = form.cleaned_data["description"]
            collection.is_private = form.cleaned_data["is_private"]
            collection.items.set(items)
            if collection.is_private and items:
                CollectionItem.objects.filter(
                    item__in=items, collection__is_private=False
                ).delete()

            collection.allowed_users.set(form.cleaned_data["allowed_users"])

            new_image = form.cleaned_data.get("image")
            if new_image:
                if collection.image:
                    collection.image.delete(save=False)
                collection.image = new_image

            collection.save()
            messages.success(
                request,
                f"Collection '{collection.title}' has been updated successfully.",
            )
            return redirect("gear:collection_detail", collection_id=collection.id)

    else:
        form = CollectionForm(
            initial={
                "title": collection.title,
                "description": collection.description,
                "is_private": collection.is_private,
                "items": collection.items.all(),
                "allowed_users": collection.allowed_users.all(),
            },
            user=request.user,
        )

    return render(
        request, "detail/collection_edit.html", {"form": form, "collection": collection}
    )


@user_passes_test(is_librarian, login_url="gear:home")
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.method == "POST":
        title = collection.title
        collection.delete()
        messages.success(
            request, f"Collection '{title}' has been deleted successfully."
        )
        return redirect("gear:home")

    return render(request, "detail/collection_delete.html", {"object": collection})


@user_passes_test(is_patron, login_url="gear:home")
def request_private_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection.is_private:
        messages.info(
            request, "This collection is public and does not require a request."
        )
        return redirect("gear:collection_detail", collection_id=collection.id)

    if request.method == "POST":
        try:
            _patron_service.request_private_collection(collection, request.user)
            messages.success(
                request, "Your access request has been submitted successfully."
            )
        except Exception as e:
            messages.error(request, str(e))
        return redirect("gear:collection_detail", collection_id=collection.id)

    return render(
        request, "detail/request_private_collections.html", {"collection": collection}
    )
