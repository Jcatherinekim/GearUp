from django.shortcuts import redirect, render
from gear.forms.add_library_form import LibraryForm
from gear.views.base import is_librarian
from django.contrib.auth.decorators import user_passes_test
from gear.service.service_instances import _library_service

from django.contrib import messages


@user_passes_test(is_librarian, login_url="gear:home")
def add_library(request):
    if request.method == "POST":
        form = LibraryForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            library_data = form.cleaned_data
            image = request.FILES.get("image")
            items = form.cleaned_data.get("items")
            library_data["items"] = items
            collections = form.cleaned_data.get("collections")
            library_data["collections"] = collections
            result = _library_service.create_library(library_data, request.user, image)

            if isinstance(result, Exception):
                form.add_error(None, result)
                messages.error(request, "Failed to create library. Please try again.")
            else:
                messages.success(
                    request,
                    f"Library '{library_data.get('title', 'Untitled')}' created successfully!",
                )
                return redirect("gear:library_detail", library_id=result.id)
    else:
        form = LibraryForm(user=request.user)

    context = {
        "form": form,
    }

    return render(request, "add/add_library.html", context)
