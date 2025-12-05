from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from gear.forms.add_collection_form import CollectionForm
from gear.service.service_instances import _collection_service
from gear.views.base import is_patron

from django.contrib import messages


@user_passes_test(lambda u: u.is_authenticated)
def add_collection(request):
    if request.method == "POST":
        form = CollectionForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            collection_data = form.cleaned_data
            image = request.FILES.get("image")
            allowed_users = form.cleaned_data.get("allowed_users")
            collection_data["allowed_users"] = allowed_users
            result = _collection_service.create_collection(
                collection_data, request.user, image
            )

            if isinstance(result, Exception):
                form.add_error(None, result)
                messages.error(
                    request, "Failed to create collection. Please try again."
                )
            else:
                messages.success(request, "Collection created successfully!")
                return redirect("gear:collection_detail", result.id)

    else:
        form = CollectionForm(user=request.user)

    context = {
        "form": form,
        "is_patron": is_patron(request.user),
    }

    return render(request, "add/add_collection.html", context)
