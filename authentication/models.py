
# from django.contrib.auth.models import AbstractUser
# from django.db import models
# from django.utils.translation import gettext_lazy as _


# class User(AbstractUser):
#     """
#     Custom User Model with extended fields for church management
#     """
    
#     class Role(models.TextChoices):
#         """User roles in the system"""
#         SUPER_ADMIN = 'super_admin', _('Super Admin')
#         DENOMINATION_ADMIN = 'denomination_admin', _('Denomination Admin')
#         CHURCH_ADMIN = 'church_admin', _('Church Admin')
#         MEMBER = 'member', _('Member')
    
#     # Extended fields
#     email = models.EmailField(_('email address'), unique=True)
#     phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
#     profile_image = models.ImageField(
#         _('profile image'),
#         upload_to='profiles/%Y/%m/',
#         blank=True,
#         null=True
#     )
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username']
    
    
#     # Role and permissions
#     role = models.CharField(
#         _('role'),
#         max_length=20,
#         choices=Role.choices,
#         default=Role.MEMBER
#     )
    
#     # Relationships
#     denomination = models.ForeignKey(
#         'denomination.Denomination',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='users',
#         verbose_name=_('denomination')
#     )
#     church_branch = models.ForeignKey(
#         'denomination.ChurchBranch',
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='users',
#         verbose_name=_('church branch')
#     )
    
    
#     # Account status
#     is_verified = models.BooleanField(_('verified'), default=False)
#     is_active = models.BooleanField(_('active'), default=True)
    
#     # Timestamps
#     created_at = models.DateTimeField(_('created at'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
#     # Make email the primary login field
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
#     class Meta:
#         db_table = 'users'
#         verbose_name = _('user')
#         verbose_name_plural = _('users')
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"{self.get_full_name()} ({self.email})"
    
#     def get_full_name(self):
#         """Return user's full name"""
#         return f"{self.first_name} {self.last_name}".strip() or self.username
    
#     def is_super_admin(self):
#         """Check if user is super admin"""
#         return self.role == self.Role.SUPER_ADMIN
    
#     def is_denomination_admin(self):
#         """Check if user is denomination admin"""
#         return self.role == self.Role.DENOMINATION_ADMIN
    
#     def is_church_admin(self):
#         """Check if user is church admin"""
#         return self.role == self.Role.CHURCH_ADMIN
    
#     def is_admin(self):
#         """Check if user has any admin role"""
#         return self.role in [
#             self.Role.SUPER_ADMIN,
#             self.Role.DENOMINATION_ADMIN,
#             self.Role.CHURCH_ADMIN
#         ]


# class UserProfile(models.Model):
#     """
#     Extended user profile information
#     Separate model for additional user data
#     """
    
#     class Gender(models.TextChoices):
#         MALE = 'male', _('Male')
#         FEMALE = 'female', _('Female')
#         OTHER = 'other', _('Other')
    
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name='profile'
#     )
    
#     # Personal information
#     gender = models.CharField(
#         _('gender'),
#         max_length=10,
#         choices=Gender.choices,
#         blank=True,
#         null=True
#     )
#     date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
#     address = models.TextField(_('address'), blank=True)
#     city = models.CharField(_('city'), max_length=100, blank=True)
#     state = models.CharField(_('state'), max_length=100, blank=True)
#     country = models.CharField(_('country'), max_length=100, default='Nigeria')
    
#     # Church information
#     department = models.CharField(_('department'), max_length=100, blank=True)
#     joined_date = models.DateField(_('date joined church'), blank=True, null=True)
    
#     # Additional contact
#     emergency_contact_name = models.CharField(_('emergency contact name'), max_length=200, blank=True)
#     emergency_contact_phone = models.CharField(_('emergency contact phone'), max_length=20, blank=True)
    
#     # Bio
#     bio = models.TextField(_('biography'), blank=True, max_length=500)
    
#     # Timestamps
#     created_at = models.DateTimeField(_('created at'), auto_now_add=True)
#     updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
#     class Meta:
#         db_table = 'user_profiles'
#         verbose_name = _('user profile')
#         verbose_name_plural = _('user profiles')
    
#     def __str__(self):
#         return f"Profile of {self.user.get_full_name()}"
    
#     @property
#     def age(self):
#         """Calculate user's age"""
#         if self.date_of_birth:
#             from datetime import date
#             today = date.today()
#             return today.year - self.date_of_birth.year - (
#                 (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
#             )
#         return None


"""
User and Authentication Models
Custom user model with role-based access control
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import secrets


class User(AbstractUser):
    """
    Custom User Model with extended fields for church management
    """
    
    class Role(models.TextChoices):
        """User roles in the system"""
        SUPER_ADMIN = 'super_admin', _('Super Admin')
        DENOMINATION_ADMIN = 'denomination_admin', _('Denomination Admin')
        CHURCH_ADMIN = 'church_admin', _('Church Admin')
        MEMBER = 'member', _('Member')
    
    # Extended fields
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True, null=True)
    profile_image = models.ImageField(
        _('profile image'),
        upload_to='profiles/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Role and permissions
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    
    # Relationships
    denomination = models.ForeignKey(
        'denomination.Denomination',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('denomination')
    )
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('church branch')
    )
    
    # Account status
    is_verified = models.BooleanField(_('verified'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Make email the primary login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return user's full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def is_super_admin(self):
        """Check if user is super admin"""
        return self.role == self.Role.SUPER_ADMIN
    
    def is_denomination_admin(self):
        """Check if user is denomination admin"""
        return self.role == self.Role.DENOMINATION_ADMIN
    
    def is_church_admin(self):
        """Check if user is church admin"""
        return self.role == self.Role.CHURCH_ADMIN
    
    def is_admin(self):
        """Check if user has any admin role"""
        return self.role in [
            self.Role.SUPER_ADMIN,
            self.Role.DENOMINATION_ADMIN,
            self.Role.CHURCH_ADMIN
        ]


class UserProfile(models.Model):
    """
    Extended user profile information
    Separate model for additional user data
    """
    
    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHER = 'other', _('Other')
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Personal information
    gender = models.CharField(
        _('gender'),
        max_length=10,
        choices=Gender.choices,
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    address = models.TextField(_('address'), blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state = models.CharField(_('state'), max_length=100, blank=True)
    country = models.CharField(_('country'), max_length=100, default='Nigeria')
    
    # Church information
    department = models.CharField(_('department'), max_length=100, blank=True)
    joined_date = models.DateField(_('date joined church'), blank=True, null=True)
    
    # Additional contact
    emergency_contact_name = models.CharField(_('emergency contact name'), max_length=200, blank=True)
    emergency_contact_phone = models.CharField(_('emergency contact phone'), max_length=20, blank=True)
    
    # Bio
    bio = models.TextField(_('biography'), blank=True, max_length=500)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
    
    @property
    def age(self):
        """Calculate user's age"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class EmailVerificationToken(models.Model):
    """
    Email verification tokens
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.user.email}"
    
    @staticmethod
    def generate_token():
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        """Check if token is still valid"""
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()


class PasswordResetToken(models.Model):
    """
    Password reset tokens
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reset token for {self.user.email}"
    
    @staticmethod
    def generate_token():
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        """Check if token is still valid"""
        from django.utils import timezone
        return not self.used and self.expires_at > timezone.now()
    
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save()