from django.shortcuts import render
from gear.service.service_instances import _item_service
from django.shortcuts import redirect
from gear.models import Item
from gear.models import WishlistEntry
from django.contrib.auth.decorators import login_required, user_passes_test
from gear.views.base import is_patron
from django.contrib import messages


@user_passes_test(is_patron, login_url='gear:home')
def wishlist(request):
    wishlist_items = _item_service.get_all_wishlist_items(request.user)
    context = {
        'wishlist_items': wishlist_items,
    }
    print(wishlist_items)
    return render(request, 'wishlist/wishlist.html', context)


@login_required
def remove_from_wishlist(request, item_id):
    if request.method == 'POST':
        item = Item.objects.get(id=item_id)
        WishlistEntry.objects.filter(user_profile=request.user.userprofile, item_id=item_id).delete()
        messages.success(request, f"'{item.title}' has been removed from your wishlist.")
    return redirect('users:wishlist')