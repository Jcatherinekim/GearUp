from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from gear.models import CollectionAccessRequest
from gear.views.base import is_librarian
from users.service.librarian.librarian_service import LibrarianService


@user_passes_test(is_librarian, login_url="gear:home")
def librarian_private_collections(request):
    if not is_librarian(request.user):
        return HttpResponseForbidden("You don't have permission to access this page.")

    requests_qs = (
        CollectionAccessRequest.objects.all()
        .order_by("-request_date")
        .select_related("collection", "patron", "approved_by")
    )
    pending_requests = requests_qs.filter(status="pending")
    approved_requests = requests_qs.filter(status="approved")
    rejected_requests = requests_qs.filter(status="rejected")

    context = {
        "requests": requests_qs,
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "pending_count": pending_requests.count(),
        "approved_count": approved_requests.count(),
        "rejected_count": rejected_requests.count(),
    }

    return render(request, "requests/librarian/private_collections.html", context)


@user_passes_test(is_librarian, login_url="gear:home")
def approve_private_collection_request(request, request_id):
    if not is_librarian(request.user):
        return HttpResponseForbidden("You don't have permission to approve requests.")

    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)
    if access_request.status != "pending":
        messages.error(request, "Only pending requests can be approved.")
        return redirect("users:librarian_private_collections")

    result = LibrarianService.approve_private_collection_request(
        access_request, request.user.userprofile
    )
    if result is True:
        messages.success(
            request,
            f"Private collection request for '{access_request.collection.title}' has been approved.",
        )
    else:
        messages.error(request, f"Failed to approve request: {result}")

    return redirect("users:librarian_private_collections")


@user_passes_test(is_librarian, login_url="gear:home")
def deny_private_collection_request(request, request_id):
    if not is_librarian(request.user):
        return HttpResponseForbidden("You don't have permission to deny requests.")

    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)
    if access_request.status != "pending":
        messages.error(request, "Only pending requests can be denied.")
        return redirect("users:librarian_private_collections")

    result = LibrarianService.deny_private_collection_request(
        access_request, request.user.userprofile
    )
    if result is True:
        messages.success(
            request,
            f"Private collection request for '{access_request.collection.title}' has been denied.",
        )
    else:
        messages.error(request, f"Failed to deny request: {result}")

    return redirect("users:librarian_private_collections")
