from django.forms import ValidationError
from ...models import UserProfile as User
from django.utils import timezone
from datetime import timedelta


class LibrarianService:
    @staticmethod
    def is_librarian(user: User) -> bool:
        if not user.is_authenticated:
            return False

        if not hasattr(user, "userprofile"):
            return False

        return user.userprofile.user_type == "librarian"

    @staticmethod
    def get_all_librarians():
        return User.objects.filter(user_type="librarian")

    @staticmethod
    def promote_to_librarian(librarians_data, user) -> bool:
        try:
            new_librarians = librarians_data.pop("new_librarians")
            for librarian in new_librarians:
                if librarian.user_type != "librarian":
                    librarian.user_type = "librarian"
                    librarian.full_clean()
                    librarian.save()
            return True
        except (ValidationError, ValueError, User.DoesNotExist) as e:
            return e

    @staticmethod
    def demote_librarian(librarians_data, user) -> bool:
        try:
            librarians_to_demote = librarians_data.pop("librarians_to_demote")
            for librarian in librarians_to_demote:
                if librarian.user_type == "librarian":
                    librarian.user_type = "patron"
                    librarian.full_clean()
                    librarian.save()
            return True
        except (ValidationError, ValueError, User.DoesNotExist) as e:
            return e

    @staticmethod
    def approve_rental_request(rental_request, librarian):
        from gear.models import BorrowHistory

        try:
            if rental_request.status != "pending":
                return "Only pending requests can be approved"

            if rental_request.quantity > rental_request.item.available_quantity:
                return (
                    f"Not enough quantity available. Requested: {rental_request.quantity}, "
                    f"Available: {rental_request.item.available_quantity}"
                )

            rental_request.status = "approved"
            rental_request.approved_by = librarian
            rental_request.approved_date = timezone.now()
            rental_request.save()

            item = rental_request.item
            item.rent_start_date = rental_request.approved_date
            item.rent_return_date = rental_request.approved_date + timedelta(days=7)

            for _ in range(rental_request.quantity):
                BorrowHistory.objects.create(
                    item=item,
                    user=rental_request.patron,
                )

            if item.available_quantity == 0:
                item.status = "rented_out"

            item.save(update_fields=["rent_start_date", "rent_return_date", "status"])
            return True

        except Exception as e:
            return str(e)

    @staticmethod
    def deny_rental_request(rental_request, librarian):
        try:
            if rental_request.status != "pending":
                return "Only pending requests can be denied"

            rental_request.status = "rejected"
            rental_request.approved_by = librarian
            rental_request.approved_date = timezone.now()
            rental_request.save()

            return True
        except Exception as e:
            return str(e)

    @staticmethod
    def approve_private_collection_request(access_request, librarian):
        try:
            if access_request.status != "pending":
                return "Only pending requests can be approved."
            access_request.status = "approved"
            access_request.approved_by = librarian
            access_request.approved_date = timezone.now()
            access_request.save()
            if not access_request.collection.allowed_users.filter(
                id=access_request.patron.id
            ).exists():
                access_request.collection.allowed_users.add(access_request.patron)
            return True
        except Exception as e:
            return str(e)

    @staticmethod
    def deny_private_collection_request(access_request, librarian):
        try:
            if access_request.status != "pending":
                return "Only pending requests can be denied."
            access_request.status = "rejected"
            access_request.approved_by = librarian
            access_request.approved_date = timezone.now()
            access_request.save()
            return True
        except Exception as e:
            return str(e)
