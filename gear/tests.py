from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from django.contrib.auth.models import User
from django.db import models
from django.contrib.messages import get_messages
import uuid

from gear.models import (
    ItemReview,
    Library,
    Item,
    ItemImage,
    BorrowHistory,
    WishlistEntry,
    Collection,
    CollectionItem,
    RentalRequest,
)
from users.models import UserProfile
from gear.service.item.item_service import ItemService


class ItemServiceTest(TestCase):
    def setUp(self):
        # Create Django User first
        self.django_user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password123"
        )
        # Then create UserProfile linked to the User
        self.user = UserProfile.objects.create(
            user=self.django_user, email="test@example.com", name="Test User"
        )

    def test_create_item_service(self):
        """Test item creation through the service layer"""

        item_data = {
            "title": "Service Test Item",
            "location": "in_store",
            "description": "A test item created through service",
            "created_by": self.user,
        }

        # Create a user to pass to the service
        auth_user = User.objects.create_user(
            username="service_test", password="password123"
        )
        auth_user.userprofile = self.user

        # Call the service method
        result = ItemService.create_item(item_data, auth_user)

        # Check that it returned an item, not an exception
        self.assertNotIsInstance(result, Exception)

        # Verify the item was created with correct attributes
        self.assertEqual(result.title, "Service Test Item")
        self.assertEqual(result.location, "in_store")
        self.assertEqual(result.description, "A test item created through service")
        self.assertEqual(result.created_by, self.user)

        # Verify an image was created for the item
        self.assertEqual(result.images.count(), 1)

    def test_get_all_items(self):
        """Test retrieving all items through the service"""

        # Create test items
        Item.objects.create(title="Item 1", location="in_store", created_by=self.user)
        Item.objects.create(title="Item 2", location="online", created_by=self.user)

        # Call the service method
        items = ItemService.get_all_items()

        # Verify both items are returned
        self.assertEqual(items.count(), 2)
        self.assertIn("Item 1", [item.title for item in items])
        self.assertIn("Item 2", [item.title for item in items])

    def test_get_items_not_in_collection(self):
        """Test retrieving items not in any collection"""

        # Create a collection
        library = Library.objects.create(title="Test Library", created_by=self.user)
        collection = Collection.objects.create(
            title="Test Collection", created_by=self.user
        )
        collection.libraries.add(library)

        # Create items - one in collection, one not
        item1 = Item.objects.create(
            title="Collection Item", location="in_store", created_by=self.user
        )
        item2 = Item.objects.create(
            title="Free Item", location="online", created_by=self.user
        )

        # Add item1 to the collection
        CollectionItem.objects.create(item=item1, collection=collection)

        # Call the service method
        free_items = ItemService.get_all_items_not_in_collection()

        # Verify only item2 is returned
        self.assertEqual(free_items.count(), 1)
        self.assertEqual(free_items.first().title, "Free Item")


class ItemDetailViewTest(TestCase):
    def setUp(self):
        # Create Django User first
        self.django_user = User.objects.create_user(
            username="detailuser", email="detail@example.com", password="password123"
        )
        # Then create UserProfile linked to the User
        self.user = UserProfile.objects.create(
            user=self.django_user, email="detail@example.com", name="Test User"
        )
        self.item = Item.objects.create(
            title="Test Item",
            location="in_store",
            description="A test item",
            created_by=self.user,
        )

    def test_item_detail_view(self):
        """Test the item detail view displays correct information"""

        client = Client()
        # Use reverse to get the correct URL
        url = reverse("gear:item_detail", kwargs={"item_id": self.item.id})
        response = client.get(url)

        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that the item is in the context
        self.assertEqual(response.context["item"], self.item)

        # Check that the item title is on the page
        self.assertContains(response, "Test Item")


class HomeViewTest(TestCase):
    def setUp(self):
        # Create Django User first
        self.django_user = User.objects.create_user(
            username="homeuser", email="home@example.com", password="password123"
        )
        # Then create UserProfile linked to the User
        self.user = UserProfile.objects.create(
            user=self.django_user, email="home@example.com", name="Test User"
        )
        self.library = Library.objects.create(
            title="Test Library", description="A test library", created_by=self.user
        )
        self.collection = Collection.objects.create(
            title="Test Collection",
            description="A test collection",
            created_by=self.user,
            is_private=False,
        )
        self.collection.libraries.add(self.library)
        self.item = Item.objects.create(
            title="Test Item",
            location="in_store",
            description="A test item",
            created_by=self.user,
        )

    def test_home_view(self):
        """Test that the home view displays all gear items"""

        client = Client()
        # Use reverse to get the correct URL
        url = reverse("gear:home")
        response = client.get(url)

        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that all gear types are in the context
        self.assertEqual(len(response.context["libraries"]), 1)
        self.assertEqual(len(response.context["collections"]), 1)
        self.assertEqual(len(response.context["items"]), 1)

        # Check that all gear is combined in the all_gear list
        self.assertEqual(len(response.context["all_gear"]), 3)

        # Check that items' titles are on the page
        self.assertContains(response, "Test Library")
        self.assertContains(response, "Test Collection")
        self.assertContains(response, "Test Item")


class ItemModelTest(TestCase):
    def setUp(self):
        # Create Django User first
        self.django_user = User.objects.create_user(
            username="modeluser", email="model@example.com", password="password123"
        )
        # Then create UserProfile linked to the User
        self.user = UserProfile.objects.create(
            user=self.django_user, email="model@example.com", name="Test User"
        )

        # Create Django User for library creator
        self.library_django_user = User.objects.create_user(
            username="libraryuser", email="library@example.com", password="password123"
        )
        # Then create UserProfile linked to the User
        self.library_user = UserProfile.objects.create(
            user=self.library_django_user,
            email="library@example.com",
            name="Library User",
        )

        self.library = Library.objects.create(
            title="Test Library",
            description="A test library",
            created_by=self.library_user,
        )
        self.item = Item.objects.create(
            title="Test Item",
            location="in_store",
            description="A test item",
            created_by=self.user,
        )
        self.item.libraries.add(self.library)

    # def test_item_current_rating(self):
    #     """Test the current_rating property without ratings"""
    #     self.assertEqual(self.item.current_rating, 0)

    #     # Add ratings
    #     ItemReview.objects.create(item=self.item, user=self.user, value=4)
    #     # Reload item from DB
    #     self.item.refresh_from_db()
    #     self.assertEqual(self.item.current_rating, 4)

    #     # Add another rating with a new user
    #     django_user2 = User.objects.create_user(
    #         username="testuser2", email="test2@example.com", password="password123"
    #     )
    #     user2 = UserProfile.objects.create(
    #         user=django_user2, email="test2@example.com", name="Test User 2"
    #     )
    #     Rating.objects.create(item=self.item, user=user2, value=2)
    #     # Reload item from DB
    #     self.item.refresh_from_db()
    #     self.assertEqual(self.item.current_rating, 3)  # (4+2)/2 = 3


class LibraryModelTest(TestCase):
    def setUp(self):
        # Create Django User first
        self.django_user = User.objects.create_user(
            username="librarymodeluser",
            email="librarymodel@example.com",
            password="password123",
        )
        # Then create UserProfile linked to the User
        self.user = UserProfile.objects.create(
            user=self.django_user, email="librarymodel@example.com", name="Test User"
        )
        self.library = Library.objects.create(
            title="Test Library", description="A test library", created_by=self.user
        )


class BorrowHistoryTest(TestCase):
    def setUp(self):
        # Create test users
        self.django_user = User.objects.create_user(
            username="borrower", email="borrower@example.com", password="password123"
        )
        self.user = UserProfile.objects.create(
            user=self.django_user, email="borrower@example.com", name="Borrower User"
        )
        
        # Create a test item
        self.item = Item.objects.create(
            title="Borrowed Item",
            location="in_store",
            description="An item to be borrowed",
            created_by=self.user,
        )

    def test_create_borrow_record(self):
        """Test creating a new borrow record"""
        borrow = BorrowHistory.objects.create(
            item=self.item,
            user=self.user,
            borrowed_at=timezone.now()
        )
        
        self.assertEqual(borrow.item, self.item)
        self.assertEqual(borrow.user, self.user)
        self.assertIsNone(borrow.returned_at)

    def test_return_item(self):
        """Test returning a borrowed item"""
        borrow = BorrowHistory.objects.create(
            item=self.item,
            user=self.user,
            borrowed_at=timezone.now()
        )
        
        # Return the item
        return_date = timezone.now() + timedelta(days=5)
        borrow.returned_at = return_date
        borrow.save()
        
        self.assertIsNotNone(borrow.returned_at)

    def test_overdue_status(self):
        """Test checking if an item is overdue"""
        past_date = timezone.now() - timedelta(days=7)
        borrow = BorrowHistory.objects.create(
            item=self.item,
            user=self.user,
            borrowed_at=past_date
        )
        
        # Set a return date in the past
        borrow.returned_at = timezone.now()
        borrow.save()
        
        # Check that the item was returned
        self.assertIsNotNone(borrow.returned_at)

    def test_active_borrows(self):
        """Test getting active borrows for a user"""
        # Create multiple borrows
        BorrowHistory.objects.create(
            item=self.item,
            user=self.user,
            borrowed_at=timezone.now()
        )
        
        # Create another item and borrow
        item2 = Item.objects.create(
            title="Another Item",
            location="in_store",
            created_by=self.user
        )
        BorrowHistory.objects.create(
            item=item2,
            user=self.user,
            borrowed_at=timezone.now()
        )
        
        active_borrows = BorrowHistory.objects.filter(
            user=self.user,
            returned_at__isnull=True
        )
        self.assertEqual(active_borrows.count(), 2)


class ItemReviewTest(TestCase):
    def setUp(self):
        # Create test users
        self.django_user = User.objects.create_user(
            username="reviewer", email="reviewer@example.com", password="password123"
        )
        self.user = UserProfile.objects.create(
            user=self.django_user, email="reviewer@example.com", name="Reviewer User"
        )
        
        # Create a test item
        self.item = Item.objects.create(
            title="Reviewed Item",
            location="in_store",
            description="An item to be reviewed",
            created_by=self.user,
        )

    def test_create_review(self):
        """Test creating a new review"""
        review = ItemReview.objects.create(
            item=self.item,
            user=self.user,
            rating=4,
            comment="Great item, works perfectly!"
        )
        
        self.assertEqual(review.item, self.item)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, "Great item, works perfectly!")

    def test_update_review(self):
        """Test updating an existing review"""
        review = ItemReview.objects.create(
            item=self.item,
            user=self.user,
            rating=4,
            comment="Initial review"
        )
        
        # Update the review
        review.rating = 5
        review.comment = "Updated review after more use"
        review.save()
        
        updated_review = ItemReview.objects.get(id=review.id)
        self.assertEqual(updated_review.rating, 5)
        self.assertEqual(updated_review.comment, "Updated review after more use")

    def test_average_rating(self):
        """Test calculating average rating for an item"""
        # Create multiple reviews
        ItemReview.objects.create(
            item=self.item,
            user=self.user,
            rating=4,
            comment="Good"
        )
        
        # Create another user and review
        django_user2 = User.objects.create_user(
            username="reviewer2", email="reviewer2@example.com", password="password123"
        )
        user2 = UserProfile.objects.create(
            user=django_user2, email="reviewer2@example.com", name="Second Reviewer"
        )
        
        ItemReview.objects.create(
            item=self.item,
            user=user2,
            rating=2,
            comment="Not so good"
        )
        
        # Calculate average rating
        avg_rating = ItemReview.objects.filter(item=self.item).aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating']
        
        self.assertEqual(avg_rating, 3.0)  # (4 + 2) / 2 = 3


class CollectionTest(TestCase):
    def setUp(self):
        # Create test users
        self.django_user = User.objects.create_user(
            username="collector", email="collector@example.com", password="password123"
        )
        self.user = UserProfile.objects.create(
            user=self.django_user, email="collector@example.com", name="Collector User"
        )
        
        # Create a test library
        self.library = Library.objects.create(
            title="Test Library",
            description="A test library",
            created_by=self.user
        )
        
        # Create a test collection
        self.collection = Collection.objects.create(
            title="Test Collection",
            description="A test collection",
            created_by=self.user,
            is_private=False
        )
        self.collection.libraries.add(self.library)

    def test_add_item_to_collection(self):
        """Test adding an item to a collection"""
        item = Item.objects.create(
            title="Collection Item",
            location="in_store",
            created_by=self.user
        )
        
        collection_item = CollectionItem.objects.create(
            item=item,
            collection=self.collection
        )
        
        self.assertEqual(collection_item.item, item)
        self.assertEqual(collection_item.collection, self.collection)
        self.assertEqual(self.collection.items.count(), 1)

    def test_remove_item_from_collection(self):
        """Test removing an item from a collection"""
        item = Item.objects.create(
            title="Collection Item",
            location="in_store",
            created_by=self.user
        )
        
        collection_item = CollectionItem.objects.create(
            item=item,
            collection=self.collection
        )
        
        # Remove the item
        collection_item.delete()
        
        self.assertEqual(self.collection.items.count(), 0)

    def test_collection_privacy(self):
        """Test collection privacy settings"""
        # Create a private collection
        private_collection = Collection.objects.create(
            title="Private Collection",
            description="A private collection",
            created_by=self.user,
            is_private=True
        )
        
        self.assertTrue(private_collection.is_private)
        
        # Create another user
        django_user2 = User.objects.create_user(
            username="viewer", email="viewer@example.com", password="password123"
        )
        user2 = UserProfile.objects.create(
            user=django_user2, email="viewer@example.com", name="Viewer User"
        )
        
        # Test that public collection is visible to other users
        public_collections = Collection.objects.filter(is_private=False)
        self.assertIn(self.collection, public_collections)
        
        # Test that private collection is not visible to other users
        public_collections = Collection.objects.filter(is_private=False)
        self.assertNotIn(private_collection, public_collections)

    def test_collection_items_count(self):
        """Test counting items in a collection"""
        # Add multiple items
        for i in range(3):
            item = Item.objects.create(
                title=f"Item {i}",
                location="in_store",
                created_by=self.user
            )
            CollectionItem.objects.create(
                item=item,
                collection=self.collection
            )
        
        self.assertEqual(self.collection.items.count(), 3)


class RentalRequestTests(TestCase):
    def setUp(self):
        # Create users
        self.patron_user = User.objects.create_user(
            username='testpatron',
            password='testpass123'
        )
        self.patron_profile = UserProfile.objects.create(
            user=self.patron_user,
            name='Test Patron',
            email='patron@test.com',
            user_type='patron'
        )

        self.librarian_user = User.objects.create_user(
            username='testlibrarian',
            password='testpass123'
        )
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian_user,
            name='Test Librarian',
            email='librarian@test.com',
            user_type='librarian'
        )

        # Create test item
        self.item = Item.objects.create(
            id=uuid.uuid4(),
            title='Test Item',
            description='Test Description',
            quantity=5,
            location='Test Location'
        )

        # Create client
        self.client = Client()

    def test_patron_create_rental_request(self):
        """Test creating a rental request as a patron"""
        self.client.login(username='testpatron', password='testpass123')
        
        response = self.client.post(
            reverse('users:request_rent_item', args=[self.item.id]),
            {'quantity': 2}
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('gear:home'))
        
        # Check if request was created
        self.assertTrue(RentalRequest.objects.filter(
            patron=self.patron_profile,
            item=self.item,
            quantity=2,
            status='pending'
        ).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), f"Rental request created for {self.item.title}!")

    def test_patron_create_duplicate_request(self):
        """Test creating a duplicate rental request"""
        self.client.login(username='testpatron', password='testpass123')
        
        # Create initial request
        RentalRequest.objects.create(
            patron=self.patron_profile,
            item=self.item,
            quantity=1,
            status='pending'
        )
        
        # Try to create duplicate request
        response = self.client.post(
            reverse('users:request_rent_item', args=[self.item.id]),
            {'quantity': 1}
        )
        
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("already have a pending request", str(messages[0]))

    def test_patron_cancel_request(self):
        """Test canceling a rental request"""
        self.client.login(username='testpatron', password='testpass123')
        
        # Create request to cancel
        request = RentalRequest.objects.create(
            patron=self.patron_profile,
            item=self.item,
            quantity=1,
            status='pending'
        )
        
        response = self.client.post(
            reverse('users:cancel_rental_request', args=[request.id])
        )
        
        # Check if request was deleted
        self.assertFalse(RentalRequest.objects.filter(id=request.id).exists())
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            f"Request for '{self.item.title}' has been cancelled."
        )

    def test_librarian_approve_request(self):
        """Test approving a rental request as a librarian and verify BorrowHistory."""
        self.client.login(username='testlibrarian', password='testpass123')
        
        # Create request to approve for quantity 2
        request_quantity = 2
        request = RentalRequest.objects.create(
            patron=self.patron_profile,
            item=self.item,
            quantity=request_quantity,
            status='pending'
        )
        
        # Check initial BorrowHistory count
        initial_bh_count = BorrowHistory.objects.filter(user=self.patron_profile, item=self.item).count()
        
        response = self.client.post(
            reverse('users:approve_rental_request', args=[request.id])
        )
        
        # Refresh request from db
        request.refresh_from_db()
        
        # Check if request was approved
        self.assertEqual(request.status, 'approved')
        self.assertEqual(request.approved_by, self.librarian_profile)
        
        # *** Add Assertions for BorrowHistory ***
        final_bh_count = BorrowHistory.objects.filter(user=self.patron_profile, item=self.item).count()
        self.assertEqual(final_bh_count, initial_bh_count + request_quantity, "BorrowHistory record count should increase by request quantity.")
        # Check one of the created records (optional, but good practice)
        new_records = BorrowHistory.objects.filter(user=self.patron_profile, item=self.item).order_by('-borrowed_at')[:request_quantity]
        for record in new_records:
            self.assertIsNone(record.returned_at, "Newly created BorrowHistory record should not have a return date.")
            self.assertEqual(record.user, self.patron_profile)
            self.assertEqual(record.item, self.item)
            
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            f"Request for '{self.item.title}' by {self.patron_profile.name} has been approved."
        )

    def test_librarian_deny_request(self):
        """Test denying a rental request as a librarian"""
        self.client.login(username='testlibrarian', password='testpass123')
        
        # Create request to deny
        request = RentalRequest.objects.create(
            patron=self.patron_profile,
            item=self.item,
            quantity=1,
            status='pending'
        )
        
        response = self.client.post(
            reverse('users:deny_rental_request', args=[request.id])
        )
        
        # Refresh request from db
        request.refresh_from_db()
        
        # Check if request was denied
        self.assertEqual(request.status, 'rejected')
        self.assertEqual(request.approved_by, self.librarian_profile)
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            f"Request for '{self.item.title}' by {self.patron_profile.name} has been denied."
        )

    def test_approve_request_insufficient_quantity(self):
        """Test approving a request with insufficient quantity"""
        self.client.login(username='testlibrarian', password='testpass123')
        
        # Create request with quantity higher than available
        request = RentalRequest.objects.create(
            patron=self.patron_profile,
            item=self.item,
            quantity=10,  # Item only has quantity of 5
            status='pending'
        )
        
        response = self.client.post(
            reverse('users:approve_rental_request', args=[request.id])
        )
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Not enough quantity available", str(messages[0]))
        
        # Check request wasn't approved
        request.refresh_from_db()
        self.assertEqual(request.status, 'pending')

    def test_unauthorized_access(self):
        """Test unauthorized access to rental request actions"""
        # Try to access librarian views as patron
        self.client.login(username='testpatron', password='testpass123')
        
        request = RentalRequest.objects.create(
            patron=self.patron_profile,
            item=self.item,
            quantity=1,
            status='pending'
        )
        
        response = self.client.post(
            reverse('users:approve_rental_request', args=[request.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirects to home
        
        # Try to access patron views as librarian
        self.client.login(username='testlibrarian', password='testpass123')
        
        response = self.client.post(
            reverse('users:request_rent_item', args=[self.item.id]),
            {'quantity': 1}
        )
        self.assertEqual(response.status_code, 302)  # Redirects to home


class BorrowingHistoryViewTests(TestCase):
    def setUp(self):
        # --- Create Users --- 
        # Patron 1
        self.patron1_django_user = User.objects.create_user(
            username='patron1', password='pass1'
        )
        self.patron1 = UserProfile.objects.create(
            user=self.patron1_django_user, name='Patron One', email='p1@test.com', user_type='patron'
        )
        # Patron 2
        self.patron2_django_user = User.objects.create_user(
            username='patron2', password='pass2'
        )
        self.patron2 = UserProfile.objects.create(
            user=self.patron2_django_user, name='Patron Two', email='p2@test.com', user_type='patron'
        )
        # Librarian
        self.librarian_django_user = User.objects.create_user(
            username='librarian', password='passlib'
        )
        self.librarian = UserProfile.objects.create(
            user=self.librarian_django_user, name='Lib Rarian', email='lib@test.com', user_type='librarian'
        )

        # --- Create Items ---
        self.item1 = Item.objects.create(title='Book A', quantity=5, location='in_store')
        self.item2 = Item.objects.create(title='Device B', quantity=2, location='in_store')
        self.item3 = Item.objects.create(title='Cable C', quantity=10, location='online')

        # --- Create Borrow History --- 
        # Patron 1: 2 Book A (current), 1 Device B (returned), 1 Cable C (current)
        self.bh1 = BorrowHistory.objects.create(user=self.patron1, item=self.item1, borrowed_at=timezone.now() - timedelta(days=5))
        self.bh2 = BorrowHistory.objects.create(user=self.patron1, item=self.item1, borrowed_at=timezone.now() - timedelta(days=4))
        self.bh3 = BorrowHistory.objects.create(user=self.patron1, item=self.item2, borrowed_at=timezone.now() - timedelta(days=10), returned_at=timezone.now() - timedelta(days=1))
        self.bh4 = BorrowHistory.objects.create(user=self.patron1, item=self.item3, borrowed_at=timezone.now() - timedelta(days=2))

        # Patron 2: 1 Book A (returned), 3 Cable C (current)
        self.bh5 = BorrowHistory.objects.create(user=self.patron2, item=self.item1, borrowed_at=timezone.now() - timedelta(days=8), returned_at=timezone.now() - timedelta(days=3))
        self.bh6 = BorrowHistory.objects.create(user=self.patron2, item=self.item3, borrowed_at=timezone.now() - timedelta(days=1))
        self.bh7 = BorrowHistory.objects.create(user=self.patron2, item=self.item3, borrowed_at=timezone.now() - timedelta(days=1))
        self.bh8 = BorrowHistory.objects.create(user=self.patron2, item=self.item3, borrowed_at=timezone.now() - timedelta(days=1))

        # --- Client Setup --- 
        self.client = Client()

    def test_patron_borrowing_history_view(self):
        """Test patron can view their grouped borrowing history."""
        self.client.login(username='patron1', password='pass1')
        url = reverse('gear:patron_borrowing_history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests/patron/borrowing_history.html')

        # Check currently borrowed items for Patron 1 (should be grouped)
        borrowed_context = response.context['currently_borrowed'] # List of dicts
        self.assertEqual(len(borrowed_context), 2) # Book A (x2), Cable C (x1)
        book_a_group = next((g for g in borrowed_context if g['item'] == self.item1), None)
        cable_c_group = next((g for g in borrowed_context if g['item'] == self.item3), None)
        self.assertIsNotNone(book_a_group)
        self.assertEqual(book_a_group['count'], 2)
        self.assertIsNotNone(cable_c_group)
        self.assertEqual(cable_c_group['count'], 1)

        # Check returned items for Patron 1 (should be grouped)
        returned_context = response.context['returned_items']
        self.assertEqual(len(returned_context), 1) # Device B (x1)
        device_b_group = next((g for g in returned_context if g['item'] == self.item2), None)
        self.assertIsNotNone(device_b_group)
        self.assertEqual(device_b_group['count'], 1)

        # Check rendered content (basic checks)
        self.assertContains(response, 'Currently Borrowed Items')
        self.assertContains(response, 'Returned Items')
        self.assertContains(response, self.item1.title) # Book A
        self.assertContains(response, 'Quantity: 2') # For Book A
        self.assertContains(response, self.item3.title) # Cable C
        self.assertContains(response, self.item2.title) # Device B (returned)
        self.assertNotContains(response, 'Quantity Returned: 1')

    def test_librarian_currently_borrowed_view(self):
        """Test librarian can view currently borrowed items, grouped by patron and item."""
        self.client.login(username='librarian', password='passlib')
        url = reverse('gear:librarian_currently_borrowed')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests/librarian/currently_borrowed.html')

        # Check context data structure (regrouped in template)
        # We check the initial list passed to the template
        grouped_items_context = response.context['grouped_borrowed_items']
        # Expected groups: (P1, Item1), (P1, Item3), (P2, Item3)
        self.assertEqual(len(grouped_items_context), 3)
        
        # Verify counts in context data
        p1_item1 = next((g for g in grouped_items_context if g['patron']==self.patron1 and g['item']==self.item1), None)
        p1_item3 = next((g for g in grouped_items_context if g['patron']==self.patron1 and g['item']==self.item3), None)
        p2_item3 = next((g for g in grouped_items_context if g['patron']==self.patron2 and g['item']==self.item3), None)
        
        self.assertIsNotNone(p1_item1)
        self.assertEqual(p1_item1['count'], 2)
        self.assertIsNotNone(p1_item3)
        self.assertEqual(p1_item3['count'], 1)
        self.assertIsNotNone(p2_item3)
        self.assertEqual(p2_item3['count'], 3)

        # Check basic rendered content
        self.assertContains(response, self.patron1.name)
        self.assertContains(response, self.patron2.name)
        # Check for item title presence within patron groups (harder to test precise grouping in HTML)
        self.assertContains(response, self.item1.title) # P1 has Book A
        self.assertContains(response, self.item3.title) # Both have Cable C
        self.assertContains(response, '>2</td>') # P1 Book A count
        self.assertContains(response, '>1</td>') # P1 Cable C count
        self.assertContains(response, '>3</td>') # P2 Cable C count
        self.assertContains(response, 'name="quantity"') # Check for the quantity input

    def test_librarian_return_items_action(self):
        """Test the action of returning a specific quantity of items."""
        self.client.login(username='librarian', password='passlib')
        url = reverse('gear:librarian_return_items')

        # --- Test returning 1 of 3 Cable C for Patron 2 --- 
        initial_borrowed_count = BorrowHistory.objects.filter(user=self.patron2, item=self.item3, returned_at__isnull=True).count()
        self.assertEqual(initial_borrowed_count, 3)
        item3_initial_status = Item.objects.get(id=self.item3.id).status

        response = self.client.post(url, {
            'patron_id': self.patron2.id,
            'item_id': self.item3.id,
            'quantity': 1
        })

        # Check redirect and success message
        self.assertRedirects(response, reverse('gear:librarian_currently_borrowed'))
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Successfully returned 1 unit(s) of '{self.item3.title}' for {self.patron2.name}", str(messages[0]))

        # Verify DB state
        returned_count = BorrowHistory.objects.filter(user=self.patron2, item=self.item3, returned_at__isnull=False).count()
        still_borrowed_count = BorrowHistory.objects.filter(user=self.patron2, item=self.item3, returned_at__isnull=True).count()
        self.assertEqual(returned_count, 1)
        self.assertEqual(still_borrowed_count, 2)
        # Item status should remain unchanged if it wasn't 'rented_out' or became available
        self.item3.refresh_from_db()
        self.assertEqual(self.item3.status, item3_initial_status) # Assuming it started available

        # --- Test returning the remaining 2 Cable C for Patron 2 --- 
        response = self.client.post(url, {
            'patron_id': self.patron2.id,
            'item_id': self.item3.id,
            'quantity': 2
        })
        self.assertRedirects(response, reverse('gear:librarian_currently_borrowed'))
        messages = list(get_messages(response.wsgi_request))
        self.assertIn(f"Successfully returned 2 unit(s) of '{self.item3.title}' for {self.patron2.name}", str(messages[0]))
        returned_count = BorrowHistory.objects.filter(user=self.patron2, item=self.item3, returned_at__isnull=False).count()
        still_borrowed_count = BorrowHistory.objects.filter(user=self.patron2, item=self.item3, returned_at__isnull=True).count()
        self.assertEqual(returned_count, 3)
        self.assertEqual(still_borrowed_count, 0)

    def test_librarian_return_items_zero_quantity(self):
        """Test returning zero quantity results in an error."""
        self.client.login(username='librarian', password='passlib')
        url = reverse('gear:librarian_return_items')
        # Setup: Ensure patron1 has 2 Book A borrowed 
        BorrowHistory.objects.filter(user=self.patron1, item=self.item1).update(returned_at=None)
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron1, item=self.item1, returned_at__isnull=True).count(), 2)
        
        response = self.client.post(url, {
            'patron_id': self.patron1.id,
            'item_id': self.item1.id,
            'quantity': 0 
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Invalid return request data", str(messages[0]))
        # Verify count hasn't changed
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron1, item=self.item1, returned_at__isnull=True).count(), 2)

    def test_librarian_return_items_too_many(self):
        """Test returning more items than borrowed results in an error."""
        self.client.login(username='librarian', password='passlib')
        url = reverse('gear:librarian_return_items')
        # Setup: Ensure patron1 has 2 Book A borrowed
        BorrowHistory.objects.filter(user=self.patron1, item=self.item1).update(returned_at=None)
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron1, item=self.item1, returned_at__isnull=True).count(), 2)

        response = self.client.post(url, {
            'patron_id': self.patron1.id,
            'item_id': self.item1.id, 
            'quantity': 3 # Requesting more than the 2 available
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1, f"Expected 1 message, got: {[str(m) for m in messages]}")
        self.assertIn(
            f"Cannot return 3 units. Only 2 unit(s) of '{self.item1.title}' are currently borrowed by {self.patron1.name}.", 
            str(messages[0]) 
        )
        # Verify count hasn't changed
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron1, item=self.item1, returned_at__isnull=True).count(), 2)

    def test_librarian_return_items_none_borrowed(self):
        """Test returning an item the patron doesn't currently have borrowed."""
        self.client.login(username='librarian', password='passlib')
        url = reverse('gear:librarian_return_items')
        # Setup: Ensure patron1 has returned all Book A
        BorrowHistory.objects.filter(user=self.patron1, item=self.item1).update(returned_at=timezone.now())
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron1, item=self.item1, returned_at__isnull=True).count(), 0)

        response = self.client.post(url, {
            'patron_id': self.patron1.id,
            'item_id': self.item1.id, 
            'quantity': 1
        })
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(
            f"No borrowed records found for {self.item1.title} by {self.patron1.name} to return", 
            str(messages[0]) 
        )

    def test_borrowing_view_access_control(self):
        """Test that patrons can't access librarian view and vice-versa."""
        # Patron tries to access librarian view
        self.client.login(username='patron1', password='pass1')
        librarian_url = reverse('gear:librarian_currently_borrowed')
        response = self.client.get(librarian_url)
        # Check for redirect status code and that the path starts with expected login/home URL
        self.assertEqual(response.status_code, 302, msg="Patron should be redirected (status code) from librarian view.")
        self.assertTrue(response.url.startswith(reverse('gear:home')), msg="Patron redirect URL should start with home URL.")
        
        # Also test the POST action endpoint
        librarian_return_url = reverse('gear:librarian_return_items')
        response = self.client.post(librarian_return_url, {'patron_id':1, 'item_id':1, 'quantity':1})
        self.assertEqual(response.status_code, 302, msg="Patron should be redirected (status code) from librarian POST view.")
        self.assertTrue(response.url.startswith(reverse('gear:home')), msg="Patron POST redirect URL should start with home URL.")

        # Librarian tries to access patron view
        self.client.login(username='librarian', password='passlib')
        patron_url = reverse('gear:patron_borrowing_history')
        response = self.client.get(patron_url)
        self.assertEqual(response.status_code, 302, msg="Librarian should be redirected (status code) from patron view.")
        self.assertTrue(response.url.startswith(reverse('gear:home')), msg="Librarian redirect URL should start with home URL.")


class SystemWorkflowTests(TestCase):
    def setUp(self):
        # --- Create Users --- 
        # Patron
        self.patron_django_user = User.objects.create_user(
            username='systempatron', password='passpat'
        )
        self.patron = UserProfile.objects.create(
            user=self.patron_django_user, name='System Patron', email='sysp@test.com', user_type='patron'
        )
        # Librarian
        self.librarian_django_user = User.objects.create_user(
            username='systemlibrarian', password='passlibsys'
        )
        self.librarian = UserProfile.objects.create(
            user=self.librarian_django_user, name='System Lib Rarian', email='syslib@test.com', user_type='librarian'
        )

        # --- Create Item ---
        self.item_workflow = Item.objects.create(title='Workflow Test Item', quantity=3, location='in_store')

        # --- Client Setup --- 
        self.client = Client()

    def test_full_rental_workflow(self):
        """Test the end-to-end flow: Request -> Approve -> Check History."""
        request_quantity = 2

        # === 1. Patron requests item ===
        self.client.login(username='systempatron', password='passpat')
        request_url = reverse('users:request_rent_item', args=[self.item_workflow.id])
        response_request = self.client.post(request_url, {'quantity': request_quantity})
        
        # Check redirect and message
        self.assertRedirects(response_request, reverse('gear:home'))
        messages_request = list(get_messages(response_request.wsgi_request))
        self.assertEqual(len(messages_request), 1)
        self.assertIn(f"Rental request created for {self.item_workflow.title}!", str(messages_request[0]))

        # Verify RentalRequest exists
        rental_request = RentalRequest.objects.filter(patron=self.patron, item=self.item_workflow).first()
        self.assertIsNotNone(rental_request)
        self.assertEqual(rental_request.status, 'pending')
        self.assertEqual(rental_request.quantity, request_quantity)
        self.client.logout()

        # === 2. Librarian approves request === 
        self.client.login(username='systemlibrarian', password='passlibsys')
        approve_url = reverse('users:approve_rental_request', args=[rental_request.id])
        response_approve = self.client.post(approve_url)

        # Check redirect and message
        # Note: Default redirect for approve/deny seems to be users:librarian_rentals
        self.assertRedirects(response_approve, reverse('users:librarian_rentals')) 
        messages_approve = list(get_messages(response_approve.wsgi_request))
        self.assertEqual(len(messages_approve), 1)
        self.assertIn(f"Request for '{self.item_workflow.title}' by {self.patron.name} has been approved.", str(messages_approve[0]))

        # Verify RentalRequest status updated
        rental_request.refresh_from_db()
        self.assertEqual(rental_request.status, 'approved')

        # Verify BorrowHistory records created
        bh_records = BorrowHistory.objects.filter(user=self.patron, item=self.item_workflow, returned_at__isnull=True)
        self.assertEqual(bh_records.count(), request_quantity)
        self.client.logout()

        # === 3. Patron checks their history ===
        self.client.login(username='systempatron', password='passpat')
        history_url = reverse('gear:patron_borrowing_history')
        response_history = self.client.get(history_url)

        self.assertEqual(response_history.status_code, 200)
        # Check context for the grouped item
        borrowed_context = response_history.context['currently_borrowed']
        self.assertEqual(len(borrowed_context), 1)
        workflow_item_group = borrowed_context[0]
        self.assertEqual(workflow_item_group['item'], self.item_workflow)
        self.assertEqual(workflow_item_group['count'], request_quantity)

        # Check basic rendering
        self.assertContains(response_history, self.item_workflow.title)
        self.assertContains(response_history, f'Quantity: {request_quantity}')
        self.client.logout()

    def test_full_return_workflow(self):
        """Test the end-to-end flow: Librarian returns -> Patron checks History."""
        borrow_quantity = 2
        return_quantity = 1

        # === 1. Setup: Create existing borrow records ===
        # Ensure item starts as available
        self.item_workflow.status = 'available'
        self.item_workflow.save()
        # Create borrow history records directly
        bh_list = []
        for _ in range(borrow_quantity):
            bh = BorrowHistory.objects.create(user=self.patron, item=self.item_workflow)
            bh_list.append(bh)
        # Manually update item status if necessary based on borrowing all
        # Note: available_quantity property handles the check
        if self.item_workflow.available_quantity <= 0:
             self.item_workflow.status = 'rented_out'
             self.item_workflow.save()
        
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron, item=self.item_workflow, returned_at__isnull=True).count(), borrow_quantity)

        # === 2. Librarian returns item(s) ===
        self.client.login(username='systemlibrarian', password='passlibsys')
        return_url = reverse('gear:librarian_return_items')
        response_return = self.client.post(return_url, {
            'patron_id': self.patron.id,
            'item_id': self.item_workflow.id,
            'quantity': return_quantity
        })

        # Check redirect and message
        self.assertRedirects(response_return, reverse('gear:librarian_currently_borrowed'))
        messages_return = list(get_messages(response_return.wsgi_request))
        self.assertEqual(len(messages_return), 1)
        self.assertIn(f"Successfully returned {return_quantity} unit(s) of '{self.item_workflow.title}' for {self.patron.name}", str(messages_return[0]))

        # Verify DB state
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron, item=self.item_workflow, returned_at__isnull=False).count(), return_quantity)
        self.assertEqual(BorrowHistory.objects.filter(user=self.patron, item=self.item_workflow, returned_at__isnull=True).count(), borrow_quantity - return_quantity)
        # Verify item status updated (should be available now)
        self.item_workflow.refresh_from_db()
        self.assertEqual(self.item_workflow.status, 'available')
        self.client.logout()

        # === 3. Patron checks their history ===
        self.client.login(username='systempatron', password='passpat')
        history_url = reverse('gear:patron_borrowing_history')
        response_history = self.client.get(history_url)

        self.assertEqual(response_history.status_code, 200)

        # Check currently borrowed section
        borrowed_context = response_history.context['currently_borrowed']
        remaining_count = borrow_quantity - return_quantity
        if remaining_count > 0:
            self.assertEqual(len(borrowed_context), 1)
            workflow_item_group_borrowed = borrowed_context[0]
            self.assertEqual(workflow_item_group_borrowed['item'], self.item_workflow)
            self.assertEqual(workflow_item_group_borrowed['count'], remaining_count)
            self.assertContains(response_history, self.item_workflow.title)
            # Check quantity only shown if > 1
            if remaining_count > 1:
                self.assertContains(response_history, f'Quantity: {remaining_count}')
            else:
                pass # No assertion needed if count is 1, template logic handles it
        else:
            self.assertEqual(len(borrowed_context), 0)
            self.assertContains(response_history, "No items currently borrowed")

        # Check returned section
        returned_context = response_history.context['returned_items']
        self.assertEqual(len(returned_context), 1) # Only one group for this item type
        workflow_item_group_returned = returned_context[0]
        self.assertEqual(workflow_item_group_returned['item'], self.item_workflow)
        self.assertEqual(workflow_item_group_returned['count'], return_quantity)
        self.assertContains(response_history, "Returned Items")
        # Check quantity only shown if > 1
        if return_quantity > 1:
             self.assertContains(response_history, f'Quantity Returned: {return_quantity}')
        else:
            pass # No assertion needed if count is 1, template logic handles it

        self.client.logout()
