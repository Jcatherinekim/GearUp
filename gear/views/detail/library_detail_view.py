from django.shortcuts import render, get_object_or_404
from gear.models import Library, Collection, Item

from users.service.service_instances import _librarian_service, _patron_service
from django.shortcuts import redirect
from gear.forms.add_library_form import LibraryForm
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from gear.service.service_instances import _item_service
from django.db.models import Q

def is_librarian(user):
    return _librarian_service.is_librarian(user)

def is_patron(user):
    return _patron_service.is_patron(user)

def library_detail(request, library_id):
    user = request.user
    library = get_object_or_404(Library, id=library_id)
    
    # Get search and filter parameters
    content_search_query = request.GET.get('content_search', '')
    current_filter = request.GET.get('filter', 'all') # Default to 'all'

    # Initial querysets
    if user.is_authenticated:
        collections_qs = Collection.objects.filter(libraries=library)
    else:
        collections_qs = Collection.objects.filter(libraries=library, is_private=False)
    items_qs = library.items.all()

    # Apply search filter first
    if content_search_query:
        collections_qs = collections_qs.filter(
            Q(title__icontains=content_search_query) |
            Q(description__icontains=content_search_query)
        )
        items_qs = items_qs.filter(
            Q(title__icontains=content_search_query) |
            Q(description__icontains=content_search_query)
        )

    # Apply type filter (after search)
    if current_filter == 'collections':
        items_qs = Item.objects.none() # Clear items if filtering for collections
    elif current_filter == 'items':
        collections_qs = Collection.objects.none() # Clear collections if filtering for items

    # Prefetch related collections for items before passing to context
    items_qs = items_qs.prefetch_related('collections')

    user_is_librarian = user.is_authenticated and is_librarian(user)
    user_is_creator = user.is_authenticated and (user == library.created_by)
    user_has_access = False

    """if user.is_authenticated and hasattr(user, "userprofile"):
        user_has_access = library.allowed_users.filter(
            id=user.userprofile.id
        ).exists()"""

    context = {
        "library": library,
        "collections": collections_qs, # Use potentially filtered queryset
        "items": items_qs, # Use potentially filtered queryset
        "user_is_librarian": user_is_librarian,
        "user_is_creator": user_is_creator,
        "user_has_access": user_has_access,
        "content_search_query": content_search_query, 
        "current_filter": current_filter, # Pass the active filter
    }
    return render(request, "detail/library_detail.html", context)

@user_passes_test(is_librarian, login_url="gear:home")
def edit_library(request, library_id):
    library = get_object_or_404(Library, id=library_id)

    # Get search queries from GET parameters
    item_search_query = request.GET.get('item_search', '')
    collection_search_query = request.GET.get('collection_search', '')

    if request.method == "POST":
        # Pass user and search queries to the form
        form = LibraryForm(request.POST, request.FILES, user=request.user, 
                           item_search_query=item_search_query, 
                           collection_search_query=collection_search_query)

        if form.is_valid():
            library.title = form.cleaned_data["title"]
            library.description = form.cleaned_data["description"]
            library.collections.set(form.cleaned_data["collections"])
            library.items.set(form.cleaned_data["items"])

            if form.cleaned_data.get("image"):
                if library.image:
                    library.image.delete(save=False)
                library.image = form.cleaned_data["image"]

            library.save()
            messages.success(request, f"Library '{library.title}' has been updated successfully.")
            return redirect("gear:library_detail", library_id=library.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pass user and search queries to the form for initial rendering
        form = LibraryForm(
            initial={
                "title": library.title,
                "description": library.description,
                "collections": library.collections.all(),
                "items": library.items.all(),
            },
            user=request.user,
            item_search_query=item_search_query, 
            collection_search_query=collection_search_query
        )

    # Add search queries to context for the template
    context = {
        "form": form,
        "library": library, # Pass library for context
        "item_search_query": item_search_query,
        "collection_search_query": collection_search_query,
    }

    return render(
        request,
        "detail/library_edit.html",
        context
    )

@user_passes_test(is_librarian, login_url="gear:home")
def delete_library(request, library_id):
    library = get_object_or_404(Library, id=library_id)

    if request.method == "POST":
        library.delete()
        messages.success(request, f"Library '{library.title}' has been deleted successfully.")
        return redirect("gear:home")

    return render(
        request,
        "detail/library_delete.html",
        {"library": library},
    )

