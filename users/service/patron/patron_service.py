from ...models import UserProfile as User
from django.db.models import Q
from django.utils import timezone


class PatronService:
    @staticmethod
    def is_patron(user) -> bool:
        if hasattr(user, "user_type"):
            return user.user_type == "patron"

        if not getattr(user, "is_authenticated", False):
            return False

        if not hasattr(user, "userprofile"):
            return False

        return user.userprofile.user_type == "patron"

    @staticmethod
    def search_patrons(query: str):
        if not query:
            return User.objects.none()

        users = User.objects.filter(
            Q(user_type="patron")
            & (Q(name__icontains=query) | Q(email__icontains=query))
        )

        return users

    @staticmethod
    def get_all_patrons():
        return User.objects.filter(user_type="patron")

    @staticmethod
    def request_rent_item(item, patron, quantity=1):
        from gear.models import RentalRequest

        if RentalRequest.objects.filter(
            patron=patron.userprofile, item=item, status="pending"
        ).exists():
            raise RentalRequestError(
                "You already have a pending request for this item."
            )

        if item.available_quantity < quantity:
            raise RentalRequestError("Requested quantity exceeds the available stock.")

        rental_request = RentalRequest.objects.create(
            item=item,
            patron=patron.userprofile,
            status="pending",
            quantity=quantity,
        )
        return rental_request

    @staticmethod
    def request_private_collection(collection, patron):
        from gear.models import CollectionAccessRequest

        if CollectionAccessRequest.objects.filter(
            patron=patron.userprofile, collection=collection, status="pending"
        ).exists():
            raise CollectionAccessRequestError(
                "You already have a pending request for this collection."
            )

        if collection.allowed_users.filter(id=patron.userprofile.id).exists():
            raise CollectionAccessRequestError(
                "You already have access to this collection."
            )

        access_request = CollectionAccessRequest.objects.create(
            collection=collection, patron=patron.userprofile, status="pending"
        )
        return access_request

    @staticmethod
    def leave_review(item, patron, rating, comment):

        from gear.models import ItemReview

        try:
            rating_value = int(rating)
        except (ValueError, TypeError):
            raise ValueError(
                "Invalid rating value; it must be an integer between 1 and 5."
            )
        if rating_value < 1 or rating_value > 5:
            raise ValueError("Rating must be between 1 and 5.")

        if ItemReview.objects.filter(item=item, user=patron.userprofile).exists():
            raise ValueError("You have already left a review for this item.")

        review = ItemReview.objects.create(
            item=item,
            user=patron.userprofile,
            rating=rating_value,
            comment=comment.strip(),
        )
        return review, True

    @staticmethod
    def get_unread_request_notifications(user):
        from gear.models import RentalRequest, CollectionAccessRequest

        up = getattr(user, "userprofile", user)

        last_rental = up.last_viewed_rental_requests or timezone.make_aware(
            timezone.datetime.min
        )
        last_coll = up.last_viewed_collection_requests or timezone.make_aware(
            timezone.datetime.min
        )

        rental_unread = RentalRequest.objects.filter(
            patron=up,
            status__in=["approved", "rejected"],
            approved_date__gt=last_rental,
        ).count()

        coll_unread = CollectionAccessRequest.objects.filter(
            patron=up, status__in=["approved", "rejected"], approved_date__gt=last_coll
        ).count()

        return rental_unread + coll_unread


class RentalRequestError(Exception):
    pass


class CollectionAccessRequestError(Exception):
    pass
