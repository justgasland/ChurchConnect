"""
MediaHub Models
Handles sermons, music, books, and other media content
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class MediaCategory(models.Model):
    """
    Categories for media items
    Example: Worship, Teaching, Testimony, Devotional
    """
    
    name = models.CharField(_('category name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    slug = models.SlugField(_('slug'), max_length=120, unique=True, blank=True)
    
    # Parent category (for subcategories)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('parent category')
    )
    
    # Visibility
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Display order
    order = models.PositiveIntegerField(_('display order'), default=0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'media_categories'
        verbose_name = _('media category')
        verbose_name_plural = _('media categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MediaTag(models.Model):
    """
    Tags for media items
    Example: Faith, Hope, Love, Healing, Prosperity
    """
    
    name = models.CharField(_('tag name'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=60, unique=True, blank=True)
    
    class Meta:
        db_table = 'media_tags'
        verbose_name = _('media tag')
        verbose_name_plural = _('media tags')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MediaItem(models.Model):
    """
    Main media item model (sermons, music, books, etc.)
    """
    
    class MediaType(models.TextChoices):
        SERMON = 'sermon', _('Sermon')
        MUSIC = 'music', _('Music/Song')
        BOOK = 'book', _('Book/E-book')
        VIDEO = 'video', _('Video')
        PODCAST = 'podcast', _('Podcast')
        DEVOTIONAL = 'devotional', _('Devotional')
        TESTIMONY = 'testimony', _('Testimony')
        OTHER = 'other', _('Other')
    
    class Visibility(models.TextChoices):
        PUBLIC = 'public', _('Public')
        MEMBERS_ONLY = 'members_only', _('Members Only')
        BRANCH_ONLY = 'branch_only', _('Branch Only')
        PRIVATE = 'private', _('Private')
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')
    
    # Basic Information
    title = models.CharField(_('title'), max_length=300)
    slug = models.SlugField(_('slug'), max_length=320, unique=True, blank=True)
    description = models.TextField(_('description'))
    
    # Classification
    media_type = models.CharField(
        _('media type'),
        max_length=20,
        choices=MediaType.choices
    )
    
    category = models.ForeignKey(
        MediaCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_items',
        verbose_name=_('category')
    )
    
    tags = models.ManyToManyField(
        MediaTag,
        blank=True,
        related_name='media_items',
        verbose_name=_('tags')
    )
    
    # Church & Denomination
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.CASCADE,
        related_name='media_items',
        verbose_name=_('church branch')
    )
    
    denomination = models.ForeignKey(
        'denomination.Denomination',
        on_delete=models.CASCADE,
        related_name='media_items',
        null=True,
        blank=True,
        verbose_name=_('denomination')
    )
    
    # Content Details
    author = models.CharField(_('author/speaker'), max_length=200)
    minister = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ministered_media',
        verbose_name=_('minister (if user)')
    )
    
    # Date
    recorded_date = models.DateField(_('recorded date'), null=True, blank=True)
    published_date = models.DateField(_('published date'), null=True, blank=True)
    
    # Media Files
    thumbnail = models.ImageField(
        _('thumbnail'),
        upload_to='media/thumbnails/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Audio file
    audio_file = models.FileField(
        _('audio file'),
        upload_to='media/audio/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg', 'm4a', 'aac'])]
    )
    
    # Video file
    video_file = models.FileField(
        _('video file'),
        upload_to='media/video/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])]
    )
    
    # Document file (for books, PDFs)
    document_file = models.FileField(
        _('document file'),
        upload_to='media/documents/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'epub', 'mobi', 'doc', 'docx'])]
    )
    
    # External links (YouTube, Vimeo, etc.)
    external_video_url = models.URLField(_('external video URL'), blank=True)
    external_audio_url = models.URLField(_('external audio URL'), blank=True)
    
    # File metadata
    file_size = models.BigIntegerField(_('file size (bytes)'), null=True, blank=True)
    duration = models.PositiveIntegerField(
        _('duration (seconds)'),
        null=True,
        blank=True,
        help_text=_('Duration for audio/video')
    )
    
    # Additional Info
    series = models.CharField(_('series name'), max_length=200, blank=True)
    series_number = models.PositiveIntegerField(_('series number'), null=True, blank=True)
    scripture_references = models.TextField(
        _('scripture references'),
        blank=True,
        help_text=_('Bible verses referenced')
    )
    
    # Language
    language = models.CharField(
        _('language'),
        max_length=50,
        default='English'
    )
    
    # Visibility & Status
    visibility = models.CharField(
        _('visibility'),
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Download & Streaming
    allow_download = models.BooleanField(_('allow download'), default=True)
    download_count = models.PositiveIntegerField(_('download count'), default=0)
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    play_count = models.PositiveIntegerField(_('play count'), default=0)
    
    # Uploader
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_media',
        verbose_name=_('uploaded by')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'media_items'
        verbose_name = _('media item')
        verbose_name_plural = _('media items')
        ordering = ['-published_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()})"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug and set denomination"""
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while MediaItem.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-set denomination from church branch
        if self.church_branch and not self.denomination:
            self.denomination = self.church_branch.denomination
        
        # Calculate file size if file exists
        if self.audio_file and not self.file_size:
            self.file_size = self.audio_file.size
        elif self.video_file and not self.file_size:
            self.file_size = self.video_file.size
        elif self.document_file and not self.file_size:
            self.file_size = self.document_file.size
        
        super().save(*args, **kwargs)
    
    @property
    def duration_formatted(self):
        """Format duration as HH:MM:SS"""
        if not self.duration:
            return None
        
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self):
        """Format file size in human-readable format"""
        if not self.file_size:
            return None
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.2f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.2f} TB"
    
    @property
    def has_audio(self):
        """Check if item has audio"""
        return bool(self.audio_file or self.external_audio_url)
    
    @property
    def has_video(self):
        """Check if item has video"""
        return bool(self.video_file or self.external_video_url)
    
    @property
    def has_document(self):
        """Check if item has document"""
        return bool(self.document_file)


class MediaPlaylist(models.Model):
    """
    Playlists/Collections of media items
    """
    
    class Visibility(models.TextChoices):
        PUBLIC = 'public', _('Public')
        PRIVATE = 'private', _('Private')
    
    name = models.CharField(_('playlist name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    slug = models.SlugField(_('slug'), max_length=220, unique=True, blank=True)
    
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.CASCADE,
        related_name='media_playlists',
        verbose_name=_('church branch')
    )
    
    media_items = models.ManyToManyField(
        MediaItem,
        through='PlaylistItem',
        related_name='playlists',
        verbose_name=_('media items')
    )
    
    thumbnail = models.ImageField(
        _('playlist thumbnail'),
        upload_to='media/playlists/%Y/%m/',
        blank=True,
        null=True
    )
    
    visibility = models.CharField(
        _('visibility'),
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_playlists',
        verbose_name=_('created by')
    )
    
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'media_playlists'
        verbose_name = _('media playlist')
        verbose_name_plural = _('media playlists')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def item_count(self):
        """Get total items in playlist"""
        return self.playlist_items.count()


class PlaylistItem(models.Model):
    """
    Through model for playlist items with ordering
    """
    
    playlist = models.ForeignKey(
        MediaPlaylist,
        on_delete=models.CASCADE,
        related_name='playlist_items',
        verbose_name=_('playlist')
    )
    
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name='playlist_memberships',
        verbose_name=_('media item')
    )
    
    order = models.PositiveIntegerField(_('order'), default=0)
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)
    
    class Meta:
        db_table = 'playlist_items'
        verbose_name = _('playlist item')
        verbose_name_plural = _('playlist items')
        ordering = ['order', 'added_at']
        unique_together = ['playlist', 'media_item']
    
    def __str__(self):
        return f"{self.media_item.title} in {self.playlist.name}"


class MediaFavorite(models.Model):
    """
    User favorites/bookmarks
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_favorites',
        verbose_name=_('user')
    )
    
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_('media item')
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'media_favorites'
        verbose_name = _('media favorite')
        verbose_name_plural = _('media favorites')
        ordering = ['-created_at']
        unique_together = ['user', 'media_item']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.media_item.title}"


class MediaComment(models.Model):
    """
    Comments on media items
    """
    
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('media item')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_comments',
        verbose_name=_('user')
    )
    
    comment = models.TextField(_('comment'))
    
    # Parent comment (for replies)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_('parent comment')
    )
    
    is_approved = models.BooleanField(_('approved'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'media_comments'
        verbose_name = _('media comment')
        verbose_name_plural = _('media comments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.media_item.title}"


class MediaRating(models.Model):
    """
    User ratings for media items
    """
    
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name=_('media item')
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_ratings',
        verbose_name=_('user')
    )
    
    rating = models.PositiveIntegerField(
        _('rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating from 1 to 5 stars')
    )
    
    review = models.TextField(_('review'), blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'media_ratings'
        verbose_name = _('media rating')
        verbose_name_plural = _('media ratings')
        ordering = ['-created_at']
        unique_together = ['user', 'media_item']
    
    def __str__(self):
        return f"{self.user.get_full_name()} rated {self.media_item.title} - {self.rating}/5"