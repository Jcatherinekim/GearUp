from django.urls import path

from gear.views.detail import collection_detail_view, item_detail_view
from gear.views.home import home_view
from gear.views.requests.rentals import librarian_rental_view, patron_rental_view
from gear.views.requests.private_collection import (
    patron_private_collections_view,
    librarian_private_collections_view,
)
from gear.views.wishlist import wishlist_view
from .views import base_view
from .views.librarian import add_librarian_view
from .views import profile_view

app_name = "users"

urlpatterns = [
    path("logout/", base_view.logout_view, name="logout"),
    path("profile/", profile_view.profile, name="profile"),
    path("librarian/add/", add_librarian_view.add_librarian, name="add_librarian"),
    path("update_profile/", profile_view.update_user, name="update_profile"),
    path("wishlist/", wishlist_view.wishlist, name="wishlist"),
    path(
        "item/<uuid:item_id>/add_to_wishlist/",
        home_view.add_to_wishlist,
        name="add_to_wishlist",
    ),
    path(
        "wishlist/remove/<uuid:item_id>/",
        wishlist_view.remove_from_wishlist,
        name="remove_from_wishlist",
    ),
    path(
        "request_rent_item/<uuid:item_id>/",
        item_detail_view.request_rent_item,
        name="request_rent_item",
    ),
    path("patron/rentals/", patron_rental_view.patron_rentals, name="patron_rentals"),
    path(
        "requests/rentals/<uuid:request_id>/cancel/",
        patron_rental_view.cancel_request,
        name="cancel_rental_request",
    ),
    path(
        "librarian/rentals/",
        librarian_rental_view.librarian_rentals,
        name="librarian_rentals",
    ),
    path(
        "librarian/rentals/<uuid:request_id>/approve/",
        librarian_rental_view.approve_rental_request,
        name="approve_rental_request",
    ),
    path(
        "librarian/rentals/<uuid:request_id>/deny/",
        librarian_rental_view.deny_rental_request,
        name="deny_rental_request",
    ),
    path(
        "request_private_collection/<uuid:collection_id>/",
        collection_detail_view.request_private_collection,
        name="request_private_collection",
    ),
    path(
        "patron/private_collections/",
        patron_private_collections_view.patron_private_collections,
        name="patron_private_collections",
    ),
    path(
        "patron/private_collections/<uuid:request_id>/cancel/",
        patron_private_collections_view.cancel_private_collection_request,
        name="cancel_private_collection_request",
    ),
    path(
        "librarian/private_collections/",
        librarian_private_collections_view.librarian_private_collections,
        name="librarian_private_collections",
    ),
    path(
        "librarian/private_collections/<uuid:request_id>/approve/",
        librarian_private_collections_view.approve_private_collection_request,
        name="approve_private_collection_request",
    ),
    path(
        "librarian/private_collections/<uuid:request_id>/deny/",
        librarian_private_collections_view.deny_private_collection_request,
        name="deny_private_collection_request",
    ),
    path(
        "leave_review/<uuid:item_id>/",
        item_detail_view.leave_review,
        name="leave_review",
    ),
]
