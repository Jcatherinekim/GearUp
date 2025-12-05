from django.shortcuts import render, get_object_or_404
from gear.forms.request_rental_form import Request_Rental_Form
from gear.forms.review_form import ReviewForm
from gear.models import Item
from gear.views.base import is_librarian, is_patron
from users.service.patron.patron_service import PatronService, RentalRequestError
from users.service.librarian.librarian_service import LibrarianService
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from gear.forms.add_item_form import ItemForm
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test


def item_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if (
        item.collections.filter(is_private=True).exists()
        and not request.user.is_authenticated
    ):
        return redirect("gear:home")

    rental_form = Request_Rental_Form()
    review_form = ReviewForm()
    collections = item.collections.all()
    reviews = item.reviews.all().order_by("-created_at")

    user_type = None
    if request.user.is_authenticated:
        if PatronService.is_patron(request.user):
            user_type = "patron"
        elif LibrarianService.is_librarian(request.user):
            user_type = "librarian"

    context = {
        "item": item,
        "user_type": user_type,
        "rental_form": rental_form,
        "review_form": review_form,
        "reviews": reviews,
        "collections": collections,
    }
    return render(request, "detail/item_detail.html", context)


@user_passes_test(is_librarian, login_url="gear:home")
def delete_item(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)

        if request.user.userprofile.user_type != "librarian":
            return HttpResponseForbidden(
                "You do not have permission to delete this item."
            )

        title = item.title
        item.delete()
        messages.success(request, f"Item '{title}' has been deleted successfully.")
        return redirect("gear:home")

    return HttpResponseForbidden("Invalid request method.")


@user_passes_test(is_librarian, login_url="gear:home")
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)

        if form.is_valid():
            item.title = form.cleaned_data["title"]
            item.description = form.cleaned_data["description"]
            item.location = form.cleaned_data["location"]
            item.quantity = form.cleaned_data["quantity"]
            item.save()

            if request.FILES.getlist("images"):
                item.images.all().delete()
                for image in request.FILES.getlist("images"):
                    item.images.create(image=image)

            messages.success(
                request, f"Item '{item.title}' has been updated successfully."
            )
            return redirect("gear:item_detail", item_id=item.id)

    else:
        form = ItemForm(
            initial={
                "title": item.title,
                "description": item.description,
                "location": item.location,
                "quantity": item.quantity,
            }
        )

    return render(request, "detail/item_edit.html", {"form": form, "item": item})


@user_passes_test(is_patron, login_url="gear:home")
def request_rent_item(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)

        if request.user.userprofile.user_type != "patron":
            return HttpResponseForbidden(
                "You do not have permission to rent this item."
            )

        rental_form = Request_Rental_Form(request.POST)

        if not rental_form.is_valid():
            messages.error(request, "Invalid quantity specified.")
            return redirect("gear:item_detail", item_id=item.id)
        quantity_requested = rental_form.cleaned_data["quantity"]

        try:
            PatronService.request_rent_item(
                item, request.user, quantity=quantity_requested
            )
        except RentalRequestError as e:
            messages.error(request, str(e))
            referer = request.META.get("HTTP_REFERER")
            if referer:
                return redirect(referer)
            return redirect("gear:item_detail", item_id=item.id)

        messages.success(
            request,
            f"Rental request created for {item.title}!",
        )
        return redirect("gear:home")

    else:
        return HttpResponseForbidden("Invalid request method.")


@user_passes_test(is_patron, login_url="gear:home")
def leave_review(request, item_id):

    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)

        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "")

        if not rating:
            messages.error(request, "Rating is required.")
            return redirect("gear:item_detail", item_id=item.id)

        try:
            review, created = PatronService.leave_review(
                item, request.user, rating, comment
            )
        except ValueError as e:
            if "already left a review" in str(e).lower():
                messages.info(request, "You already left a review on this item")
            else:
                messages.error(request, str(e))
            return redirect("gear:item_detail", item_id=item.id)

        except Exception:
            messages.error(
                request, "An unexpected error occurred while submitting your review."
            )
            return redirect("gear:item_detail", item_id=item.id)

        messages.success(request, "Your review has been submitted.")
        return redirect("gear:item_detail", item_id=item.id)

    return HttpResponseForbidden("Invalid request method.")
