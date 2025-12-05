from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from gear.models import Item
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from gear.models import Library, Collection, Item
from django.views.decorators.http import require_POST
from gear.service.service_instances import _item_service
from gear.views.base import is_patron
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q


def home(request):
    libraries = Library.objects.all()

    # Filter collections based on user authentication status
    if request.user.is_authenticated:
        collections = Collection.objects.all()
    else:
        collections = Collection.objects.filter(is_private=False)

    items = Item.objects.all()

    # Handle search
    search_query = request.GET.get("search", "")
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        collections = collections.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
        libraries = libraries.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    if request.user.is_authenticated:
        if request.user.userprofile.user_type != "librarian":
            items = items.filter(
                ~Q(collections__is_private=True)
                | Q(
                    collections__is_private=True,
                    collections__allowed_users=request.user.userprofile,
                )
            )
    else:
        items = items.exclude(collections__is_private=True)

    items = items.distinct()

    filter_type = request.GET.get("filter", "all")

    all_gear = []

    context = {
        "libraries": libraries,
        "collections": collections,
        "items": items,
        "filter": filter_type,
        "search_query": search_query,  # Add search query to context
    }

    if filter_type == "all" or not filter_type:
        all_gear = list(libraries) + list(collections) + list(items)
    elif filter_type == "collections":
        all_gear = list(collections)
    elif filter_type == "items":
        all_gear = list(items)
    elif filter_type == "libraries":
        all_gear = list(libraries)
    elif filter_type == "custom":
        show_collections = request.GET.get("show_collections")
        show_items = request.GET.get("show_items")
        show_libraries = request.GET.get("show_libraries")

        context["show_collections"] = show_collections
        context["show_items"] = show_items
        context["show_libraries"] = show_libraries

        if show_collections:
            all_gear.extend(list(collections))
        if show_items:
            all_gear.extend(list(items))
        if show_libraries:
            all_gear.extend(list(libraries))

        if not all_gear:
            all_gear = list(collections) + list(items) + list(libraries)

    # Prefetch related collections for items before passing to context
    items = items.prefetch_related("collections")

    context["all_gear"] = all_gear

    context["debug_info"] = {
        "filter_applied": filter_type,
        "total_items": len(all_gear),
        "collections_count": len([g for g in all_gear if isinstance(g, Collection)]),
        "items_count": len([g for g in all_gear if isinstance(g, Item)]),
        "libraries_count": len([g for g in all_gear if isinstance(g, Library)]),
    }

    return render(request, "home.html", context)


@user_passes_test(is_patron, login_url="gear:home")
def add_to_wishlist(request, item_id):
    if request.method == "POST":
        item = get_object_or_404(Item, id=item_id)
        try:
            wishlist_entry, created = _item_service.add_to_wishlist(item, request.user)
            if not created:
                messages.info(request, "Item is already in your wishlist.")
            else:
                messages.success(request, "Item added to your wishlist!")
        except Exception as e:
            messages.error(
                request, "Failed to add item to your wishlist. Please try again."
            )
        return redirect(request.META.get("HTTP_REFERER", "gear:home"))
    return redirect(request.META.get("HTTP_REFERER", "gear:home"))
