from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "user_type", "email")
    actions = ["make_librarian", "make_patron"]

    def make_librarian(self, request, queryset):
        updated = queryset.update(user_type="librarian")
        self.message_user(request, f"{updated} user(s) marked as librarians.")

    make_librarian.short_description = "Mark selected users as librarians"

    def make_patron(self, request, queryset):
        updated = queryset.update(user_type="patron")
        self.message_user(request, f"{updated} user(s) marked as patrons.")

    make_patron.short_description = "Mark selected users as patrons"
