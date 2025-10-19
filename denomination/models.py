"""
Denomination and Church Branch Models
Handles the organizational structure of churches
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings


class Denomination(models.Model):
    """
    Model representing a church denomination
    Example: Catholic Church, Methodist Church, RCCG, etc.
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PENDING = 'pending', _('Pending Approval')
    
    # Basic Information
    name = models.CharField(_('denomination name'), max_length=200, unique=True)
    slug = models.SlugField(_('slug'), max_length=220, unique=True, blank=True)
    description = models.TextField(_('description'), blank=True)
    
    # Branding
    logo = models.ImageField(
        _('logo'),
        upload_to='denominations/logos/%Y/%m/',
        blank=True,
        null=True
    )
    cover_image = models.ImageField(
        _('cover image'),
        upload_to='denominations/covers/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Contact Information
    headquarters = models.CharField(_('headquarters'), max_length=300, blank=True)
    contact_email = models.EmailField(_('contact email'), blank=True)
    contact_phone = models.CharField(_('contact phone'), max_length=20, blank=True)
    website = models.URLField(_('website'), blank=True)
    
    # Social Media
    facebook_url = models.URLField(_('Facebook URL'), blank=True)
    twitter_url = models.URLField(_('Twitter URL'), blank=True)
    instagram_url = models.URLField(_('Instagram URL'), blank=True)
    youtube_url = models.URLField(_('YouTube URL'), blank=True)
    
    # Management
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_denominations',
        verbose_name=_('created by')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Settings
    allow_public_registration = models.BooleanField(
        _('allow public registration'),
        default=True,
        help_text=_('Allow people to register and join this denomination')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'denominations'
        verbose_name = _('denomination')
        verbose_name_plural = _('denominations')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def total_branches(self):
        """Get total number of branches"""
        return self.branches.filter(status=ChurchBranch.Status.ACTIVE).count()
    
    @property
    def total_members(self):
        """Get total members across all branches"""
        from django.db.models import Count
        return self.users.filter(is_active=True).count()


class ChurchBranch(models.Model):
    """
    Model representing individual church branches/locations
    """
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        UNDER_CONSTRUCTION = 'under_construction', _('Under Construction')
    
    # Relationship
    denomination = models.ForeignKey(
        Denomination,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name=_('denomination')
    )
    
    # Basic Information
    name = models.CharField(_('branch name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=220, blank=True)
    description = models.TextField(_('description'), blank=True)
    
    # Images
    image = models.ImageField(
        _('branch image'),
        upload_to='branches/images/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Location Information
    address = models.TextField(_('address'))
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=100)
    country = models.CharField(_('country'), max_length=100, default='Nigeria')
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    
    # Geolocation (for maps)
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True
    )
    
    # Contact Information
    contact_email = models.EmailField(_('contact email'))
    contact_phone = models.CharField(_('contact phone'), max_length=20)
    alternative_phone = models.CharField(_('alternative phone'), max_length=20, blank=True)
    
    # Management
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='administered_branches',
        verbose_name=_('branch admin')
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Service Times
    service_times = models.TextField(
        _('service times'),
        blank=True,
        help_text=_('Example: Sunday: 8AM, 10AM | Wednesday: 6PM')
    )
    
    # Capacity
    seating_capacity = models.PositiveIntegerField(
        _('seating capacity'),
        blank=True,
        null=True,
        help_text=_('Maximum number of people the church can accommodate')
    )
    
    # Settings
    is_headquarters = models.BooleanField(_('is headquarters'), default=False)
    allow_online_giving = models.BooleanField(_('allow online giving'), default=True)
    allow_event_registration = models.BooleanField(_('allow event registration'), default=True)
    
    # Timestamps
    established_date = models.DateField(_('established date'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'church_branches'
        verbose_name = _('church branch')
        verbose_name_plural = _('church branches')
        ordering = ['denomination', 'name']
        unique_together = ['denomination', 'slug']
    
    def __str__(self):
        return f"{self.name} - {self.denomination.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def full_address(self):
        """Get formatted full address"""
        return f"{self.address}, {self.city}, {self.state}, {self.country}"
    
    @property
    def total_members(self):
        """Get total members in this branch"""
        return self.users.filter(is_active=True).count()
    
    @property
    def google_maps_url(self):
        """Generate Google Maps URL if coordinates exist"""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None


class BranchDepartment(models.Model):
    """
    Model representing departments within a church branch
    Example: Youth Ministry, Choir, Ushering, etc.
    """
    
    branch = models.ForeignKey(
        ChurchBranch,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_('church branch')
    )
    
    name = models.CharField(_('department name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    
    # Leadership
    head = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_departments',
        verbose_name=_('department head')
    )
    
    # Contact
    contact_email = models.EmailField(_('contact email'), blank=True)
    contact_phone = models.CharField(_('contact phone'), max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'branch_departments'
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ['branch', 'name']
        unique_together = ['branch', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.branch.name}"
    
    @property
    def member_count(self):
        """Get total members in this department"""
        # We'll implement this when we create the members app
        return 0
    
