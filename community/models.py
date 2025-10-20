# community/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import User
from denomination.models import ChurchBranch


class Group(models.Model):
    """
    Church community groups (e.g., Youth, Prayer Warriors)
    """
    class Visibility(models.TextChoices):
        PUBLIC = 'public', _('Public')
        PRIVATE = 'private', _('Private')
        SECRET = 'secret', _('Secret')

    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    cover_image = models.ImageField(
        _('cover image'),
        upload_to='community/groups/%Y/%m/',
        blank=True,
        null=True
    )
    visibility = models.CharField(
        _('visibility'),
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_groups',
        verbose_name=_('created by')
    )
    church_branch = models.ForeignKey(
        ChurchBranch,
        on_delete=models.CASCADE,
        related_name='community_groups',
        verbose_name=_('church branch')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'community_groups'
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.church_branch.name})"


class GroupMember(models.Model):
    """
    Members of a group with roles
    """
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        MODERATOR = 'moderator', _('Moderator')
        MEMBER = 'member', _('Member')

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('group')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name=_('user')
    )
    role = models.CharField(
        _('role'),
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER
    )
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)

    class Meta:
        db_table = 'community_group_members'
        verbose_name = _('group member')
        verbose_name_plural = _('group members')
        unique_together = ['group', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.get_full_name()} in {self.group.name}"


class Post(models.Model):
    """
    Posts within a group
    """
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('group')
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='community_posts',
        verbose_name=_('author')
    )
    content = models.TextField(_('content'))
    media = models.FileField(
        _('media'),
        upload_to='community/posts/%Y/%m/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'community_posts'
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.get_full_name()} in {self.group.name}"


class Reaction(models.Model):
    """
    Reactions to posts (like, love, pray)
    """
    class Type(models.TextChoices):
        LIKE = 'like', _('Like')
        LOVE = 'love', _('Love')
        PRAY = 'pray', _('Pray')

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('post')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_('user')
    )
    type = models.CharField(
        _('type'),
        max_length=10,
        choices=Type.choices
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        db_table = 'community_reactions'
        verbose_name = _('reaction')
        verbose_name_plural = _('reactions')
        unique_together = ['post', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} reacted with {self.type} to post {self.post.id}"


class Comment(models.Model):
    """
    Comments on posts
    """
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('post')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('user')
    )
    content = models.TextField(_('content'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'community_comments'
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on post {self.post.id}"


class ChatMessage(models.Model):
    """
    Group chat messages
    """
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name=_('group')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages',
        verbose_name=_('sender')
    )
    message = models.TextField(_('message'))
    attachment = models.FileField(
        _('attachment'),
        upload_to='community/chat/%Y/%m/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        db_table = 'community_chat_messages'
        verbose_name = _('chat message')
        verbose_name_plural = _('chat messages')
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender.get_full_name()} in {self.group.name}"