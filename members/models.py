"""
Member Management Models
Handles member profiles, attendance, and membership records
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class MembershipType(models.Model):
    """
    Different types of membership
    Example: Regular Member, Associate Member, Honorary Member
    """
    
    name = models.CharField(_('membership type'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.CASCADE,
        related_name='membership_types',
        verbose_name=_('church branch')
    )
    
    # Privileges
    can_vote = models.BooleanField(_('can vote'), default=True)
    can_hold_office = models.BooleanField(_('can hold office'), default=True)
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'membership_types'
        verbose_name = _('membership type')
        verbose_name_plural = _('membership types')
        ordering = ['church_branch', 'name']
        unique_together = ['church_branch', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.church_branch.name}"


class Member(models.Model):
    """
    Extended member information linked to User model
    """
    
    class MemberStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        TRANSFERRED = 'transferred', _('Transferred')
        DECEASED = 'deceased', _('Deceased')
    
    class MaritalStatus(models.TextChoices):
        SINGLE = 'single', _('Single')
        MARRIED = 'married', _('Married')
        DIVORCED = 'divorced', _('Divorced')
        WIDOWED = 'widowed', _('Widowed')
    
    # Link to User
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='member_profile',
        verbose_name=_('user')
    )
    
    # Membership Information
    membership_number = models.CharField(
        _('membership number'),
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )
    membership_type = models.ForeignKey(
        MembershipType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='members',
        verbose_name=_('membership type')
    )
    
    status = models.CharField(
        _('member status'),
        max_length=20,
        choices=MemberStatus.choices,
        default=MemberStatus.ACTIVE
    )
    
    # Personal Details
    marital_status = models.CharField(
        _('marital status'),
        max_length=20,
        choices=MaritalStatus.choices,
        blank=True
    )
    occupation = models.CharField(_('occupation'), max_length=200, blank=True)
    employer = models.CharField(_('employer'), max_length=200, blank=True)
    
    # Family Information
    spouse_name = models.CharField(_('spouse name'), max_length=200, blank=True)
    anniversary_date = models.DateField(_('wedding anniversary'), blank=True, null=True)
    number_of_children = models.PositiveIntegerField(
        _('number of children'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    
    # Church Information
    baptism_date = models.DateField(_('baptism date'), blank=True, null=True)
    baptism_location = models.CharField(_('baptism location'), max_length=200, blank=True)
    confirmation_date = models.DateField(_('confirmation date'), blank=True, null=True)
    
    # Previous Church
    previous_church = models.CharField(_('previous church'), max_length=200, blank=True)
    transfer_letter = models.FileField(
        _('transfer letter'),
        upload_to='members/transfers/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Skills and Interests
    skills = models.TextField(
        _('skills/talents'),
        blank=True,
        help_text=_('e.g., Singing, Teaching, Technical skills')
    )
    interests = models.TextField(
        _('interests'),
        blank=True,
        help_text=_('Areas of interest in church activities')
    )
    
    # Membership Dates
    joined_date = models.DateField(
        _('date joined church'),
        blank=True,
        null=True
    )
    membership_approved_date = models.DateField(
        _('membership approved date'),
        blank=True,
        null=True
    )
    membership_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_memberships',
        verbose_name=_('approved by')
    )
    
    # Notes
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Private notes (only visible to admins)')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'members'
        verbose_name = _('member')
        verbose_name_plural = _('members')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.membership_number or 'No ID'}"
    
    def save(self, *args, **kwargs):
        """Auto-generate membership number if not provided"""
        if not self.membership_number and self.user.church_branch:
            # Format: BRANCH-YEAR-NUMBER (e.g., VIC-2025-001)
            branch_code = self.user.church_branch.slug[:3].upper()
            from datetime import datetime
            year = datetime.now().year
            
            # Get last member number for this branch this year
            last_member = Member.objects.filter(
                membership_number__startswith=f"{branch_code}-{year}-"
            ).order_by('-membership_number').first()
            
            if last_member and last_member.membership_number:
                try:
                    last_num = int(last_member.membership_number.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            
            self.membership_number = f"{branch_code}-{year}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def age(self):
        """Calculate member's age"""
        if hasattr(self.user, 'profile') and self.user.profile.date_of_birth:
            from datetime import date
            today = date.today()
            dob = self.user.profile.date_of_birth
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        return None
    
    @property
    def years_of_membership(self):
        """Calculate years as member"""
        if self.joined_date:
            from datetime import date
            today = date.today()
            years = today.year - self.joined_date.year
            return years if years >= 0 else 0
        return 0


class Attendance(models.Model):
    """
    Track member attendance for services and events
    """
    
    class AttendanceStatus(models.TextChoices):
        PRESENT = 'present', _('Present')
        ABSENT = 'absent', _('Absent')
        LATE = 'late', _('Late')
        EXCUSED = 'excused', _('Excused')
    
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('member')
    )
    
    church_branch = models.ForeignKey(
        'denomination.ChurchBranch',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_('church branch')
    )
    
    # Event reference (optional - we'll link to events app later)
    # event = models.ForeignKey(
    #     'events.Event',
    #     on_delete=models.CASCADE,
    #     related_name='attendances',
    #     null=True,
    #     blank=True
    # )
    
    event_name = models.CharField(
        _('event/service name'),
        max_length=200,
        help_text=_('e.g., Sunday Service, Bible Study')
    )
    
    date = models.DateField(_('attendance date'))
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT
    )
    
    # Time tracking
    check_in_time = models.DateTimeField(_('check-in time'), blank=True, null=True)
    check_out_time = models.DateTimeField(_('check-out time'), blank=True, null=True)
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    # Who recorded it
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_attendances',
        verbose_name=_('recorded by')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'attendances'
        verbose_name = _('attendance')
        verbose_name_plural = _('attendances')
        ordering = ['-date', '-check_in_time']
        unique_together = ['member', 'date', 'event_name']
    
    def __str__(self):
        return f"{self.member.user.get_full_name()} - {self.event_name} ({self.date})"
    
    @property
    def duration(self):
        """Calculate attendance duration"""
        if self.check_in_time and self.check_out_time:
            delta = self.check_out_time - self.check_in_time
            hours = delta.total_seconds() / 3600
            return round(hours, 2)
        return None


class MemberNote(models.Model):
    """
    Private notes about members (pastoral care, counseling, etc.)
    """
    
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='notes_list',
        verbose_name=_('member')
    )
    
    title = models.CharField(_('title'), max_length=200)
    content = models.TextField(_('content'))
    
    # Privacy
    is_confidential = models.BooleanField(
        _('confidential'),
        default=True,
        help_text=_('Only visible to church leadership')
    )
    
    # Author
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_member_notes',
        verbose_name=_('created by')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'member_notes'
        verbose_name = _('member note')
        verbose_name_plural = _('member notes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.member.user.get_full_name()}"


class MemberDepartment(models.Model):
    """
    Track which departments a member belongs to
    """
    
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='member_departments',
        verbose_name=_('member')
    )
    
    department = models.ForeignKey(
        'denomination.BranchDepartment',
        on_delete=models.CASCADE,
        related_name='department_members',
        verbose_name=_('department')
    )
    
    # Role in department
    role = models.CharField(
        _('role'),
        max_length=100,
        blank=True,
        help_text=_('e.g., Coordinator, Assistant, Member')
    )
    
    # Status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Dates
    joined_date = models.DateField(_('joined date'), auto_now_add=True)
    left_date = models.DateField(_('left date'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'member_departments'
        verbose_name = _('member department')
        verbose_name_plural = _('member departments')
        ordering = ['member', 'department']
        unique_together = ['member', 'department']
    
    def __str__(self):
        return f"{self.member.user.get_full_name()} - {self.department.name}"