# portal/test_critical_path.py
"""
Critical path tests for the portal app focusing on:
Registration → Email Verification → Login → App Access
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from unittest.mock import patch
import uuid

from portal.models import UserProfile, EmailVerificationToken, App, UserAppAccess
from portal.forms import RegistrationForm, LoginForm


class UserRegistrationFlowTest(TestCase):
    """Test the complete user registration and verification flow"""
    
    def setUp(self):
        self.client = Client()
        self.registration_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        # Create default apps for testing
        self.default_app = App.objects.create(
            app_id='test_app',
            name='Test App',
            description='Test application',
            icon='fa-test',
            link='/test/',
            is_default=True,
            order=1
        )
    
    def test_registration_creates_user_and_profile(self):
        """Test that registration creates user, profile, and sends verification email"""
        response = self.client.post(reverse('portal:register'), self.registration_data)
        
        # Check redirect to login page
        self.assertRedirects(response, reverse('portal:login'))
        
        # Check user was created
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertTrue(user.is_active)
        
        # Check profile was created via signal
        self.assertTrue(hasattr(user, 'profile'))
        self.assertFalse(user.profile.is_email_verified)
        
        # Check verification token was created
        self.assertTrue(hasattr(user, 'verification_token'))
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verify your email', mail.outbox[0].subject)
    
    def test_email_verification_success(self):
        """Test successful email verification"""
        # Create user and token
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, is_email_verified=False)
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        # Verify email
        response = self.client.get(
            reverse('portal:verify_email', kwargs={'token': token.token})
        )
        
        # Check redirect and success message
        self.assertRedirects(response, reverse('portal:login'))
        
        # Check profile is now verified
        user.profile.refresh_from_db()
        self.assertTrue(user.profile.is_email_verified)
        
        # Check token was deleted
        self.assertFalse(
            EmailVerificationToken.objects.filter(user=user).exists()
        )
    
    def test_login_requires_email_verification(self):
        """Test that unverified users cannot login"""
        # Create unverified user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=user, is_email_verified=False)
        
        # Attempt login
        response = self.client.post(reverse('portal:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        # Check login was rejected
        self.assertEqual(response.status_code, 200)  # Stays on login page
        self.assertContains(response, 'verify your email')
    
    def test_complete_registration_to_dashboard_flow(self):
        """Test the complete flow from registration to accessing dashboard"""
        # 1. Register
        response = self.client.post(reverse('portal:register'), self.registration_data)
        self.assertRedirects(response, reverse('portal:login'))
        
        # 2. Get verification token
        user = User.objects.get(username='testuser')
        token = user.verification_token.token
        
        # 3. Verify email
        response = self.client.get(
            reverse('portal:verify_email', kwargs={'token': token})
        )
        self.assertRedirects(response, reverse('portal:login'))
        
        # 4. Login
        response = self.client.post(reverse('portal:login'), {
            'username': 'testuser',
            'password': 'complexpassword123'
        })
        self.assertRedirects(response, reverse('portal:home'))
        
        # 5. Access dashboard
        response = self.client.get(reverse('portal:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hey, Test')  # Welcome message
        
        # 6. Check default apps were assigned
        user_app_access = UserAppAccess.objects.filter(user=user)
        self.assertTrue(user_app_access.exists())
        self.assertEqual(user_app_access.first().app, self.default_app)


class UserProfileModelTest(TestCase):
    """Test UserProfile model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_profile_created_on_user_creation(self):
        """Test that UserProfile is created when User is created"""
        # Profile should be created by signal
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertFalse(self.user.profile.is_email_verified)
    
    def test_profile_string_representation(self):
        """Test UserProfile __str__ method"""
        expected = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.user.profile), expected)


class EmailVerificationTokenTest(TestCase):
    """Test email verification token functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_token_expiration_logic(self):
        """Test token expiration checking"""
        # Create expired token
        expired_token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        self.assertTrue(expired_token.is_expired)
        
        # Create valid token
        valid_token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        self.assertFalse(valid_token.is_expired)
    
    def test_expired_token_verification_fails(self):
        """Test that expired tokens cannot be used for verification"""
        expired_token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        
        response = self.client.get(
            reverse('portal:verify_email', kwargs={'token': expired_token.token})
        )
        
        # Should redirect to login with error message
        self.assertRedirects(response, reverse('portal:login'))
        
        # Profile should still be unverified
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.is_email_verified)


class AppAccessTest(TestCase):
    """Test app access functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.profile.is_email_verified = True
        self.user.profile.save()
        
        # Create test apps
        self.default_app = App.objects.create(
            app_id='default_app',
            name='Default App',
            description='Default application',
            icon='fa-default',
            link='/default/',
            is_default=True,
            order=1
        )
        
        self.premium_app = App.objects.create(
            app_id='premium_app',
            name='Premium App',
            description='Premium application',
            icon='fa-premium',
            link='/premium/',
            is_default=False,
            order=2
        )
    
    def test_default_apps_assigned_on_user_creation(self):
        """Test that default apps are assigned to new users"""
        # Create new user (signal should assign default apps)
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        # Check default app was assigned
        user_access = UserAppAccess.objects.filter(user=new_user)
        self.assertTrue(user_access.exists())
        self.assertEqual(user_access.first().app, self.default_app)
        
        # Check premium app was NOT assigned
        self.assertFalse(
            UserAppAccess.objects.filter(user=new_user, app=self.premium_app).exists()
        )
    
    def test_home_page_shows_accessible_apps(self):
        """Test that home page only shows apps user has access to"""
        # Assign only default app
        UserAppAccess.objects.create(user=self.user, app=self.default_app)
        
        # Login and access home page
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('portal:home'))
        
        self.assertContains(response, 'Default App')
        self.assertNotContains(response, 'Premium App')


class FormValidationTest(TestCase):
    """Test form validation logic"""
    
    def test_registration_form_duplicate_email(self):
        """Test that registration form rejects duplicate emails"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='testpass123'
        )
        
        # Try to register with same email
        form_data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Duplicate email
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123'
        }
        
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Email already in use', str(form.errors))
    
    def test_login_form_validation(self):
        """Test login form validation"""
        # Valid form
        valid_form = LoginForm(data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertTrue(valid_form.is_valid())
        
        # Missing password
        invalid_form = LoginForm(data={
            'username': 'testuser',
            'password': ''
        })
        self.assertFalse(invalid_form.is_valid())


# Test runner command and GitHub Actions setup
"""
To run these tests:

1. Single test file:
   python manage.py test portal.test_critical_path

2. All portal tests:
   python manage.py test portal

3. Specific test class:
   python manage.py test portal.test_critical_path.UserRegistrationFlowTest

4. Specific test method:
   python manage.py test portal.test_critical_path.UserRegistrationFlowTest.test_complete_registration_to_dashboard_flow

5. With verbose output:
   python manage.py test portal --verbosity=2

6. Keep test database for inspection:
   python manage.py test portal --keepdb
"""