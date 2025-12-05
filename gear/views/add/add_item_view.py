from django.shortcuts import redirect, render
from django.contrib.auth.decorators import user_passes_test
from gear.forms.add_item_form import ItemForm
from gear.views.base import is_librarian
from gear.service.service_instances import _item_service

from django.contrib import messages


@user_passes_test(is_librarian, login_url="gear:home")
def add_item(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            images = request.FILES.getlist("images", None)
            result = _item_service.create_item(data, request.user, images)

            if isinstance(result, Exception):
                form.add_error(None, result)
                messages.error(request, "Failed to create item. Please try again.")
            else:
                messages.success(request, "Item created successfully!")
                return redirect("gear:item_detail", result.id)
    else:
        form = ItemForm()

    context = {
        "form": form,
    }
    return render(request, "add/add_item.html", context)
