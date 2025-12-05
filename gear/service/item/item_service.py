from django.forms import ValidationError
from gear.models import Item, ItemImage, WishlistEntry


class ItemService:

    @staticmethod
    def get_all_items():
        return Item.objects.all()

    @staticmethod
    def create_item(item_data, user, images=None):
        try:
            item_data.pop("images", None)
            item = Item(**item_data)
            item.created_by = user.userprofile
            item.full_clean()
            item.save()
            if images:
                for img in images:
                    ItemImage.objects.create(item=item, image=img)
            else:
                ItemImage.objects.create(item=item)

            return item

        except ValidationError as e:
            return e

    @staticmethod
    def get_all_items_not_in_collection():
        return Item.objects.exclude(collections__isnull=False)

    @staticmethod
    def get_items_not_in_private_collections():
        """Get all items that are not in any private collections."""
        return Item.objects.exclude(collections__is_private=True)

    @staticmethod
    def add_to_wishlist(item, user):
        wishlist_entry, created = WishlistEntry.objects.get_or_create(
            user_profile=user.userprofile,
            item=item,
        )
        return wishlist_entry, created

    @staticmethod
    def get_all_wishlist_items(user):
        return user.userprofile.wishlist_entries.all()
