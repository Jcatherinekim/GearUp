import uuid
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    profile_picture = models.ImageField(
        default="user_images/default_profile.jpg", upload_to="user_images/"
    )
    date_joined = models.DateTimeField(auto_now_add=True)

    USER_TYPE_CHOICES = [
        ("librarian", "Librarian"),
        ("patron", "Patron"),
    ]
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="patron",
    )

    last_viewed_rental_requests = models.DateTimeField(null=True, blank=True)
    last_viewed_collection_requests = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"
