from django.forms import ValidationError
from gear.models import Library


class LibraryService:
    @staticmethod
    def create_library(library_data, user, image=None):
        try:
            items = library_data.pop("items", [])
            collections = library_data.pop("collections", [])

            if library_data.get("image") is None:
                library_data.pop("image", None)

            library = Library(**library_data)
            library.created_by = user.userprofile
            library.full_clean()
            library.save()

            if items:
                library.items.set(items)

            if collections:
                library.collections.set(collections)

            if image:
                library.image = image
                library.save()

            return library
        except ValidationError as e:
            return e
