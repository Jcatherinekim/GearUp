from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from gear.models import CollectionAccessRequest
from gear.views.base import is_patron
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone


@user_passes_test(is_patron, login_url="gear:home")
def patron_private_collections(request):
    user_profile = request.user.userprofile
    user_profile.last_viewed_collection_requests = timezone.now()
    user_profile.save(update_fields=["last_viewed_collection_requests"])

    requests_qs = (
        CollectionAccessRequest.objects.filter(patron=user_profile)
        .order_by("-request_date")
        .select_related("collection")
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

    return render(request, "requests/patron/private_collections.html", context)


@user_passes_test(is_patron, login_url="gear:home")
def cancel_private_collection_request(request, request_id):
    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)

    if access_request.patron != request.user.userprofile:
        return HttpResponseForbidden(
            "You don't have permission to cancel this request."
        )

    if access_request.status != "pending":
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect("users:patron_private_collections")

    access_request.delete()
    messages.success(
        request, f"Request for '{access_request.collection.title}' has been cancelled."
    )
    return redirect("users:patron_private_collections")
