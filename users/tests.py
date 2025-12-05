# users/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core.files.storage import FileSystemStorage
from .models import UserProfile


class UserAccessTests(TestCase):
    def setUp(self):
        self.patron_profile = self.create_user_profile(
            name="Patron User",
            email="patron@example.com",
            user_type="patron",
            password="testpass123"
        )
        self.librarian_profile = self.create_user_profile(
            name="Librarian User",
            email="librarian@example.com",
            user_type="librarian",
            password="testpass123"
        )

    def create_user_profile(self, name, email, user_type, password):
        User = get_user_model()
        user = User.objects.create_user(
            username=email, email=email, password=password)
        profile = UserProfile.objects.create(
            user=user,
            name=name,
            email=email,
            user_type=user_type
        )
        return profile

    def test_librarian_can_access_add_librarian_page(self):
        self.client.force_login(self.librarian_profile.user)
        url = reverse('users:add_librarian')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'librarian/add_librarian.html')

    def test_patron_cannot_access_add_librarian_page(self):
        self.client.force_login(self.patron_profile.user)
        url = reverse('users:add_librarian')
        response = self.client.get(url)
        # A patron should be redirected
        self.assertEqual(response.status_code, 302)
        
    def test_user_can_access_profile(self):
        self.client.force_login(self.patron_profile.user)
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_user_can_logout(self):
        self.client.force_login(self.patron_profile.user)
        url = reverse('users:logout')
        response = self.client.get(url)
        # Logout should redirect
        self.assertEqual(response.status_code, 302)


class UserModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.django_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.django_user,
            name='Test User',
            email='test@example.com',
            user_type='patron'
        )
    
    def test_user_profile_creation(self):
        """Test that a user profile can be created"""
        self.assertEqual(self.user_profile.name, 'Test User')
        self.assertEqual(self.user_profile.email, 'test@example.com')
        self.assertEqual(self.user_profile.user_type, 'patron')
        
    def test_user_profile_type(self):
        """Test the user profile type"""
        # Initially a patron
        self.assertEqual(self.user_profile.user_type, 'patron')
        
        # Change user type to librarian
        self.user_profile.user_type = 'librarian'
        self.user_profile.save()
        
        # Refresh from database
        self.user_profile.refresh_from_db()
        
        # Check if the user type was updated
        self.assertEqual(self.user_profile.user_type, 'librarian')


class UserAuthenticationTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepass123'
        }
        self.user = self.User.objects.create_user(**self.user_data)
        UserProfile.objects.create(
            user=self.user,
            name='Test User',
            email=self.user_data['email'],
            user_type='patron'
        )

    def test_user_login_success(self):
        """Test successful user login"""
        login_successful = self.client.login(
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        self.assertTrue(login_successful)

    def test_user_login_wrong_password(self):
        """Test login failure with wrong password"""
        login_successful = self.client.login(
            username=self.user_data['username'],
            password='wrongpassword'
        )
        self.assertFalse(login_successful)

    def test_user_logout(self):
        """Test user logout"""
        # First login
        self.client.login(
            username=self.user_data['username'],
            password=self.user_data['password']
        )
        
        # Then logout
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)  # Should redirect after logout
        
        # Try to access a protected page
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login


class UserPermissionsTest(TestCase):
    def setUp(self):
        # Create a patron user
        self.patron_user = get_user_model().objects.create_user(
            username='patron',
            email='patron@example.com',
            password='patronpass123'
        )
        self.patron_profile = UserProfile.objects.create(
            user=self.patron_user,
            name='Patron User',
            email='patron@example.com',
            user_type='patron'
        )
        
        # Create a librarian user
        self.librarian_user = get_user_model().objects.create_user(
            username='librarian',
            email='librarian@example.com',
            password='librarianpass123'
        )
        self.librarian_profile = UserProfile.objects.create(
            user=self.librarian_user,
            name='Librarian User',
            email='librarian@example.com',
            user_type='librarian'
        )

    def test_patron_permissions(self):
        """Test patron user permissions"""
        self.client.force_login(self.patron_user)
        
        # Patron should not access librarian-only pages
        response = self.client.get(reverse('users:add_librarian'))
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Patron should access regular user pages
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)

    def test_librarian_permissions(self):
        """Test librarian user permissions"""
        self.client.force_login(self.librarian_user)
        
        # Librarian should access librarian-only pages
        response = self.client.get(reverse('users:add_librarian'))
        self.assertEqual(response.status_code, 200)
        
        # Librarian should access regular user pages
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)

    def test_permission_inheritance(self):
        """Test that librarians inherit patron permissions"""
        self.client.force_login(self.librarian_user)
        
        # Librarian should have access to all patron features
        patron_urls = [
            reverse('users:profile'),
            # Add other patron-accessible URLs here
        ]
        
        for url in patron_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class UserProfileUpdateTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='updateuser',
            email='update@example.com',
            password='updatepass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            name='Update User',
            email='update@example.com',
            user_type='patron'
        )
        self.client.force_login(self.user)

    def test_update_profile_picture(self):
        """Test updating user profile picture"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        import tempfile
        import os
        
        # Create a temporary directory for test media files
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                # Create a simple test image
                image_content = b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
                test_image = SimpleUploadedFile(
                    'test_image.gif',
                    image_content,
                    content_type='image/gif'
                )
                
                update_data = {
                    'profile_picture': test_image
                }
                
                response = self.client.post(
                    reverse('users:update_profile'),
                    update_data,
                    follow=True
                )
                
                # Refresh profile from database
                self.profile.refresh_from_db()
                
                # Check that the response was successful
                self.assertEqual(response.status_code, 200)
                # Check that a success message was shown
                messages = list(response.context['messages'])
                self.assertEqual(len(messages), 1)
                self.assertEqual(str(messages[0]), 'Profile updated successfully.')

    def test_invalid_profile_picture(self):
        """Test updating profile with invalid file type"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        import tempfile
        
        # Create a temporary directory for test media files
        with tempfile.TemporaryDirectory() as temp_dir:
            with override_settings(MEDIA_ROOT=temp_dir):
                # Create an invalid file
                invalid_file = SimpleUploadedFile(
                    'test.txt',
                    b'Invalid image content',
                    content_type='text/plain'
                )
                
                update_data = {
                    'profile_picture': invalid_file
                }
                
                response = self.client.post(
                    reverse('users:update_profile'),
                    update_data,
                    follow=True
                )
                
                # Check that the form shows validation errors
                self.assertTrue('form' in response.context)
                self.assertTrue(response.context['form'].errors)
