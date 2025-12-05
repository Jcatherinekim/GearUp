from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from gear.models import RentalRequest, BorrowHistory
from gear.views.base import is_patron
from django.contrib.auth.decorators import user_passes_test
from django.utils import timezone
from collections import defaultdict
from django.db.models import Min, Max


@user_passes_test(is_patron, login_url="gear:home")
def patron_rentals(request):
    user_profile = request.user.userprofile
    user_profile.last_viewed_rental_requests = timezone.now()
    user_profile.save(update_fields=["last_viewed_rental_requests"])
    requests = (
        RentalRequest.objects.filter(patron=user_profile)
        .order_by("-request_date")
        .select_related("item")
    )

    pending_requests = requests.filter(status="pending")
    approved_requests = requests.filter(status="approved")
    rejected_requests = requests.filter(status="rejected")

    context = {
        "requests": requests,
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "pending_count": pending_requests.count(),
        "approved_count": approved_requests.count(),
        "rejected_count": rejected_requests.count(),
    }

    return render(request, "requests/patron/rentals.html", context)


@user_passes_test(is_patron, login_url="gear:home")
def cancel_request(request, request_id):
    rental_request = get_object_or_404(RentalRequest, id=request_id)

    if rental_request.patron != request.user.userprofile:
        return HttpResponseForbidden(
            "You don't have permission to cancel this request."
        )

    if rental_request.status != "pending":
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect("users:patron_rentals")

    rental_request.delete()
    messages.success(
        request, f"Request for '{rental_request.item.title}' has been cancelled."
    )

    return redirect("users:patron_rentals")


@user_passes_test(is_patron, login_url="gear:home")
def patron_borrowing_history(request):
    patron_profile = request.user.userprofile
    
    # Get all history for the patron
    all_history = BorrowHistory.objects.filter(
        user=patron_profile
    ).select_related('item').order_by('item__title', 'borrowed_at')

    # Group currently borrowed items
    grouped_borrowed = defaultdict(lambda: {'count': 0, 'earliest_borrowed': None})
    currently_borrowed_records = all_history.filter(returned_at__isnull=True)
    for record in currently_borrowed_records:
        key = record.item
        grouped_borrowed[key]['count'] += 1
        if grouped_borrowed[key]['earliest_borrowed'] is None or record.borrowed_at < grouped_borrowed[key]['earliest_borrowed']:
            grouped_borrowed[key]['earliest_borrowed'] = record.borrowed_at

    # Group returned items
    grouped_returned = defaultdict(lambda: {'count': 0, 'latest_returned': None})
    returned_records = all_history.filter(returned_at__isnull=False).order_by('item__title', 'returned_at') # Order by returned_at for Max
    for record in returned_records:
        key = record.item
        grouped_returned[key]['count'] += 1
        if grouped_returned[key]['latest_returned'] is None or record.returned_at > grouped_returned[key]['latest_returned']:
            grouped_returned[key]['latest_returned'] = record.returned_at

    # Convert to lists of dictionaries for the template
    display_borrowed = []
    for item, data in grouped_borrowed.items():
        display_borrowed.append({
            'item': item,
            'count': data['count'],
            'earliest_borrowed': data['earliest_borrowed']
        })

    display_returned = []
    for item, data in grouped_returned.items():
        display_returned.append({
            'item': item,
            'count': data['count'],
            'latest_returned': data['latest_returned']
        })

    context = {
        'currently_borrowed': display_borrowed, # Pass grouped list
        'returned_items': display_returned, # Pass grouped list
    }
    
    return render(request, "requests/patron/borrowing_history.html", context)
