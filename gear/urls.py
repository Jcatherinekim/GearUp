from django.urls import path
from gear.views.home import home_view
from .views.add import add_item_view, add_collection_view, add_library_view
from gear.views.detail import item_detail_view, collection_detail_view
from gear.views.detail import library_detail_view
from gear.views.requests.rentals.librarian_rental_view import (
    librarian_rentals,
    approve_rental_request,
    deny_rental_request,
    currently_borrowed_items_view,
    return_items_view,
)
from gear.views.requests.private_collection.librarian_private_collections_view import (
    librarian_private_collections,
)
from gear.views.requests.rentals.patron_rental_view import (
    patron_rentals,
    patron_borrowing_history,
)

app_name = "gear"

urlpatterns = [
    path("", home_view.home, name="home"),
    path("add/item", add_item_view.add_item, name="add_item"),
    path("add/collection", add_collection_view.add_collection, name="add_collection"),
    path("add/library", add_library_view.add_library, name="add_library"),
    path("item/<uuid:item_id>/", item_detail_view.item_detail, name="item_detail"),
    path("item/<uuid:item_id>/edit/", item_detail_view.edit_item, name="item_edit"),
    path(
        "item/<uuid:item_id>/delete/", item_detail_view.delete_item, name="item_delete"
    ),
    path(
        "collections/<uuid:collection_id>/",
        collection_detail_view.collection_detail,
        name="collection_detail",
    ),
    path(
        "collection/<uuid:collection_id>/edit/",
        collection_detail_view.edit_collection,
        name="edit_collection",
    ),
    path(
        "collection/<uuid:collection_id>/delete/",
        collection_detail_view.delete_collection,
        name="delete_collection",
    ),
    path(
        "libraries/<uuid:library_id>/",
        library_detail_view.library_detail,
        name="library_detail",
    ),
    path(
        "libraries/<uuid:library_id>/edit/",
        library_detail_view.edit_library,
        name="edit_library",
    ),
    path(
        "libraries/<uuid:library_id>/delete/",
        library_detail_view.delete_library,
        name="delete_library",
    ),
    path(
        "librarian/currently-borrowed/",
        currently_borrowed_items_view,
        name="librarian_currently_borrowed",
    ),
    path(
        "librarian/return-item/",
        return_items_view,
        name="librarian_return_items",
    ),
    path(
        "patron/borrowing-history/",
        patron_borrowing_history,
        name="patron_borrowing_history",
    ),
]
