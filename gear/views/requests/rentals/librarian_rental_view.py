from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test
from gear.models import RentalRequest, BorrowHistory, Item
from gear.views.base import is_librarian
from users.service.librarian.librarian_service import LibrarianService
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from collections import defaultdict
from django.db.models import Min
from django.db import transaction
from users.models import UserProfile


@user_passes_test(is_librarian, login_url="gear:home")
def librarian_rentals(request):

    if not LibrarianService.is_librarian(request.user):
        return HttpResponseForbidden("You don't have permission to access this page.")

    requests = (
        RentalRequest.objects.all()
        .order_by("-request_date")
        .select_related("item", "patron", "approved_by")
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

    return render(request, "requests/librarian/rentals.html", context)


@user_passes_test(is_librarian, login_url="gear:home")
def currently_borrowed_items_view(request):
    # Get all unreturned borrow records, ordered for consistent grouping/display
    borrow_records = BorrowHistory.objects.filter(
        returned_at__isnull=True
    ).select_related('item', 'user').order_by(
        'user__name', 'item__title', 'borrowed_at'
    )

    # Group records by (patron, item)
    grouped_items = defaultdict(lambda: {'count': 0, 'earliest_borrowed': None, 'records': []})
    for record in borrow_records:
        key = (record.user, record.item)
        grouped_items[key]['count'] += 1
        grouped_items[key]['records'].append(record)
        if grouped_items[key]['earliest_borrowed'] is None or record.borrowed_at < grouped_items[key]['earliest_borrowed']:
            grouped_items[key]['earliest_borrowed'] = record.borrowed_at

    # Convert defaultdict to a list of dictionaries for easier template iteration
    # Each item in the list represents a unique (patron, item) group
    display_groups = []
    for (user, item), data in grouped_items.items():
        display_groups.append({
            'patron': user,
            'item': item,
            'count': data['count'],
            'earliest_borrowed': data['earliest_borrowed']
            # We don't pass the full list of records to the template anymore
        })

    context = {
        'grouped_borrowed_items': display_groups
    }
    return render(request, "requests/librarian/currently_borrowed.html", context)


@user_passes_test(is_librarian, login_url="gear:home")
def approve_rental_request(request, request_id):

    if not LibrarianService.is_librarian(request.user):
        return HttpResponseForbidden("You don't have permission to approve requests.")

    rental_request = get_object_or_404(RentalRequest, id=request_id)

    if rental_request.status != "pending":
        messages.error(request, "Only pending requests can be approved.")
        return redirect("users:librarian_rentals")

    if rental_request.quantity > rental_request.item.available_quantity:
        messages.error(
            request,
            f"Not enough quantity available. Requested: {rental_request.quantity}, Available: {rental_request.item.available_quantity}",
        )
        return redirect("users:librarian_rentals")

    result = LibrarianService.approve_rental_request(
        rental_request, request.user.userprofile
    )

    if result is True:
        messages.success(
            request,
            f"Request for '{rental_request.item.title}' by {rental_request.patron.name} has been approved.",
        )
    else:
        messages.error(request, f"Failed to approve request: {result}")

    return redirect("users:librarian_rentals")


@user_passes_test(is_librarian, login_url="gear:home")
def deny_rental_request(request, request_id):
    if not LibrarianService.is_librarian(request.user):
        return HttpResponseForbidden("You don't have permission to deny requests.")

    rental_request = get_object_or_404(RentalRequest, id=request_id)

    if rental_request.status != "pending":
        messages.error(request, "Only pending requests can be denied.")
        return redirect("users:librarian_rentals")

    result = LibrarianService.deny_rental_request(
        rental_request, request.user.userprofile
    )

    if result is True:
        messages.success(
            request,
            f"Request for '{rental_request.item.title}' by {rental_request.patron.name} has been denied.",
        )
    else:
        messages.error(request, f"Failed to deny request: {result}")

    return redirect("users:librarian_rentals")


@require_POST
@user_passes_test(is_librarian, login_url="gear:home")
def return_items_view(request):
    try:
        patron_id = request.POST.get('patron_id')
        item_id = request.POST.get('item_id')
        quantity_str = request.POST.get('quantity')

        quantity_to_return = 0
        if quantity_str and quantity_str.isdigit():
             quantity_to_return = int(quantity_str)

        if not patron_id or not item_id or quantity_to_return <= 0:
            messages.error(request, "Invalid return request data.")
            return redirect("gear:librarian_currently_borrowed")

        patron = get_object_or_404(UserProfile, id=patron_id)
        item = get_object_or_404(Item, id=item_id)

        currently_borrowed_count = BorrowHistory.objects.filter(
            user=patron, item=item, returned_at__isnull=True
        ).count()

        if currently_borrowed_count == 0:
             messages.error(request, f"No borrowed records found for {item.title} by {patron.name} to return.")
             return redirect("gear:librarian_currently_borrowed")

        if quantity_to_return > currently_borrowed_count:
             messages.error(
                 request, 
                 f"Cannot return {quantity_to_return} units. Only {currently_borrowed_count} unit(s) of '{item.title}' are currently borrowed by {patron.name}."
             )
             return redirect("gear:librarian_currently_borrowed")

        actual_returned_count = 0
        with transaction.atomic():
            records_to_return = BorrowHistory.objects.select_for_update().filter(
                user=patron, item=item, returned_at__isnull=True
            ).order_by('borrowed_at')[:quantity_to_return]

            if not records_to_return or len(records_to_return) != quantity_to_return: 
                messages.error(request, f"Could not find exactly {quantity_to_return} records to return. Please refresh and try again.")
                raise Exception("Record count mismatch during return.") 
            
            for record in records_to_return:
                record.returned_at = timezone.now()
                record.save()
                actual_returned_count += 1

            if item.available_quantity > 0 and item.status == 'rented_out':
                item.status = 'available'
                item.save(update_fields=['status'])
            
        if actual_returned_count > 0:
          messages.success(
              request,
              f"Successfully returned {actual_returned_count} unit(s) of '{item.title}' for {patron.name}."
          )
        else:
          messages.warning(request, f"Could not return items for {item.title} by {patron.name}. They may have already been returned.")

    except (ValueError, TypeError):
        messages.error(request, "Invalid quantity specified for return.")
    except UserProfile.DoesNotExist:
        messages.error(request, "Patron not found.")
    except Item.DoesNotExist:
        messages.error(request, "Item not found.")
    except Exception as e:
        # Log the exception in a real application
        print(f"DEBUG: Exception during return: {e}") # Debug print for exceptions
        messages.error(request, f"An unexpected error occurred during return: {str(e)}")

    return redirect("gear:librarian_currently_borrowed")
