import uuid
from django.db import models
from django.db.models import Avg
from django.forms import ValidationError
from users.models import UserProfile as User
from users.service.patron.patron_service import PatronService
from django.db.models.fields.files import ImageFieldFile
from django.db.models import ImageField as DjangoImageField

DEFAULT_IMAGE = "item_images/default_gear.png"


class ProtectedImageFieldFile(ImageFieldFile):
    def delete(self, save=False):
        if self.name == DEFAULT_IMAGE:
            return

        super().delete(save=save)


class ProtectedImageField(DjangoImageField):
    attr_class = ProtectedImageFieldFile


class Library(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="libraries_created",
    )
    image = ProtectedImageField(
        upload_to="item_images/",
        default=DEFAULT_IMAGE,
        blank=True,
    )
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        if self.image and self.image.name != "item_images/default_gear.png":
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def has_available_items(self):
        if self.items.filter(status="available").exists():
            return True
        return any(
            collection.has_available_items for collection in self.collections.all()
        )

    @property
    def has_rented_items(self):

        total_library_items = self.items.count()
        if total_library_items > 0:
            rented_library_items = self.items.filter(status="rented_out").count()
            if rented_library_items != total_library_items:
                return False

        collections = self.collections.all()
        if not collections.exists():
            return (
                total_library_items > 0
                and self.items.filter(status="rented_out").count()
                == total_library_items
            )

        return all(collection.has_rented_items for collection in collections)


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=200)

    identifier = models.UUIDField(default=uuid.uuid4, editable=False)

    STATUS_CHOICES = [
        ("available", "available"),
        ("rented_out", "Rented Out"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="available",
        null=False,
    )

    LOCATION_CHOICE = [
        ("in_store", "In Store"),
        ("online", "Online"),
    ]
    location = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICE,
        null=False,
    )

    description = models.TextField(blank=True)

    quantity = models.PositiveBigIntegerField(default=1)

    rent_start_date = models.DateTimeField(null=True, blank=True)
    rent_return_date = models.DateTimeField(null=True, blank=True)

    collections = models.ManyToManyField(
        "Collection", blank=True, related_name="items", through="CollectionItem"
    )

    libraries = models.ManyToManyField("Library", blank=True, related_name="items")

    borrowed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="currently_borrowed_items",
    )

    borrow_history = models.ManyToManyField(
        User, through="BorrowHistory", related_name="borrowed_items_history", blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items_created",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.quantity > 9999:
            raise ValidationError(
                {
                    "quantity": "Quantity cannot be larger than 9999. Please enter a smaller number."
                }
            )

    @property
    def in_private_collection(self):
        return self.collections.filter(is_private=True).exists()

    @property
    def in_public_collection(self):
        return self.collections.filter(is_private=False).exists()

    @property
    def current_rating(self):
        avg_rating = self.reviews.aggregate(avg_rating=Avg("rating"))["avg_rating"]
        return round(avg_rating, 2) if avg_rating is not None else 0

    def __str__(self):
        return self.title

    @property
    def get_first_image(self):
        first_image = self.images.first()
        if first_image and first_image.image:
            return first_image.image.url
        return "item_images/default_gear.png"

    @property
    def available_quantity(self):
        rented = BorrowHistory.objects.filter(
            item=self, returned_at__isnull=True
        ).count()
        return self.quantity - rented

    @property
    def is_private(self):
        return self.collections.filter(is_private=True).exists()

    @property
    def is_in_any_collection(self):
        return self.collections.exists()

    def delete(self, *args, **kwargs):
        for img in self.images.all():
            if img.image and img.image.name != "item_images/default_gear.png":
                img.image.delete(save=False)

        super().delete(*args, **kwargs)


class ItemImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="images")
    image = ProtectedImageField(
        upload_to="item_images/",
        default=DEFAULT_IMAGE,
        blank=True,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        if self.image and self.image.name != "item_images/default_gear.png":
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.item.title}"


class BorrowHistory(models.Model):

    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="borrow_history_records"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="borrow_history_records"
    )
    borrowed_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} borrowed {self.item} on {self.borrowed_at}"


class RentalRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(
        Item, on_delete=models.CASCADE, related_name="rental_requests"
    )
    patron = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rental_requests"
    )
    request_date = models.DateTimeField(auto_now_add=True)

    REQUEST_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(
        max_length=20, choices=REQUEST_STATUS_CHOICES, default="pending"
    )
    quantity = models.PositiveIntegerField(default=1)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requests",
    )
    approved_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"Request for {self.item.title} ({self.quantity} units) "
            f"by {self.patron.name} ({self.status})"
        )


class ItemReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("item", "user")

    def __str__(self):
        return f"{self.user.name} reviewed {self.item.title}: {self.rating}/5"


class WishlistEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.ForeignKey(
        "users.UserProfile", on_delete=models.CASCADE, related_name="wishlist_entries"
    )
    item = models.ForeignKey(
        "gear.Item", on_delete=models.CASCADE, related_name="wishlist_entries"
    )
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user_profile", "item")

    def __str__(self):
        return f"{self.user_profile.name} wishlisted {self.item.title}"


class Collection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    libraries = models.ManyToManyField(Library, blank=True, related_name="collections")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_private = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(
        User, blank=True, related_name="accessible_collections"
    )
    image = ProtectedImageField(
        upload_to="item_images/",
        default=DEFAULT_IMAGE,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collections_created",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        if self.image and self.image.name != "item_images/default_gear.png":
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def creator_text(self):
        if self.created_by and PatronService.is_patron(self.created_by):
            return f"Created by {self.created_by.name}"
        return "Created by GearUp"

    @property
    def has_available_items(self):
        # Check if any items are available
        return self.items.filter(status="available").exists()

    @property
    def has_rented_items(self):
        # Check if ALL items are rented out
        total_items = self.items.count()
        rented_items = self.items.filter(status="rented_out").count()
        return total_items > 0 and total_items == rented_items


class CollectionAccessRequest(models.Model):
    REQUEST_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(
        "Collection", on_delete=models.CASCADE, related_name="access_requests"
    )
    patron = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="collection_access_requests"
    )
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=REQUEST_STATUS_CHOICES, default="pending"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_collection_requests",
    )
    approved_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Access Request for {self.collection.title} by {self.patron.name} ({self.status})"


class CollectionItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("item", "collection")

    def clean(self):
        qs = CollectionItem.objects.filter(item=self.item)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if self.collection.is_private and qs.exists():
            raise ValidationError(
                "Item already belongs to a collection; cannot add it to a private collection."
            )
        if (
            not self.collection.is_private
            and qs.filter(collection__is_private=True).exists()
        ):
            raise ValidationError(
                "Item already belongs to a private collection; cannot add it to another collection."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.title} in {self.collection.title}"
