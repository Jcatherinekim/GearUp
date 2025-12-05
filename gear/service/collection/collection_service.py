from django.forms import ValidationError
from gear.models import Collection, CollectionItem


class CollectionService:
    @staticmethod
    def create_collection(collection_data, user, image=None):
        try:
            items = collection_data.pop("items", [])
            allowed_users = collection_data.pop("allowed_users", [])
            collection_data.pop("image", None)

            collection = Collection(**collection_data)
            collection.created_by = user.userprofile
            collection.full_clean()
            collection.save()

            if allowed_users:
                collection.allowed_users.set(allowed_users)

            if collection.is_private and items:

                CollectionItem.objects.filter(
                    item__in=items, collection__is_private=False
                ).delete()

            if items:
                for item in items:
                    CollectionItem.objects.create(collection=collection, item=item)

            if image:
                collection.image = image
                collection.save()

            return collection

        except ValidationError as e:
            return e

    @staticmethod
    def get_all_collections():
        return Collection.objects.all()
