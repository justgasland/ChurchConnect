"""
Serializers for Member Management
"""

from rest_framework import serializers
from django.db.models import Count, Q
from datetime import date, timedelta

from .models import (
    MembershipType,
    Member,
    Attendance,
    MemberNote,
    MemberDepartment
)
from authentication.serializers import UserSerializer
from denomination.serializers import BranchDepartmentSerializer


class MembershipTypeSerializer(serializers.ModelSerializer):
    """Serializer for membership types"""
    
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MembershipType
        fields = [
            'id', 'name', 'description', 'church_branch',
            'can_vote', 'can_hold_office', 'is_active',
            'member_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_member_count(self, obj):
        """Get total members with this type"""
        return obj.members.filter(status=Member.MemberStatus.ACTIVE).count()


class MemberDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for member department relationships"""
    
    department = BranchDepartmentSerializer(read_only=True)
    department_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = MemberDepartment
        fields = [
            'id', 'department', 'department_id', 'role',
            'is_active', 'joined_date', 'left_date'
        ]
        read_only_fields = ['id', 'joined_date']


class MemberListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing members"""
    
    user = UserSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    years_of_membership = serializers.ReadOnlyField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'user', 'membership_number', 'status',
            'age', 'years_of_membership', 'joined_date', 'created_at'
        ]
        read_only_fields = ['id', 'membership_number', 'created_at']


class MemberDetailSerializer(serializers.ModelSerializer):
    """Full serializer for member details"""
    
    user = UserSerializer(read_only=True)
    membership_type_detail = MembershipTypeSerializer(source='membership_type', read_only=True)
    departments = MemberDepartmentSerializer(source='member_departments', many=True, read_only=True)
    
    age = serializers.ReadOnlyField()
    years_of_membership = serializers.ReadOnlyField()
    
    # Statistics
    total_attendances = serializers.SerializerMethodField()
    attendance_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'user', 'membership_number', 'membership_type',
            'membership_type_detail', 'status', 'marital_status',
            'occupation', 'employer', 'spouse_name', 'anniversary_date',
            'number_of_children', 'baptism_date', 'baptism_location',
            'confirmation_date', 'previous_church', 'transfer_letter',
            'skills', 'interests', 'joined_date', 'membership_approved_date',
            'membership_approved_by', 'notes', 'age', 'years_of_membership',
            'departments', 'total_attendances', 'attendance_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'membership_number', 'created_at', 'updated_at']
    
    def get_total_attendances(self, obj):
        """Get total attendance count"""
        return obj.attendances.filter(status=Attendance.AttendanceStatus.PRESENT).count()
    
    def get_attendance_rate(self, obj):
        """Calculate attendance rate for last 90 days"""
        ninety_days_ago = date.today() - timedelta(days=90)
        total = obj.attendances.filter(date__gte=ninety_days_ago).count()
        present = obj.attendances.filter(
            date__gte=ninety_days_ago,
            status=Attendance.AttendanceStatus.PRESENT
        ).count()
        
        if total > 0:
            return round((present / total) * 100, 2)
        return 0.0


class MemberCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating members"""
    
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Member
        fields = [
            'user_id', 'membership_type', 'status', 'marital_status',
            'occupation', 'employer', 'spouse_name', 'anniversary_date',
            'number_of_children', 'baptism_date', 'baptism_location',
            'confirmation_date', 'previous_church', 'transfer_letter',
            'skills', 'interests', 'joined_date', 'notes'
        ]
    
    def validate_user_id(self, value):
        """Validate user exists and doesn't already have member profile"""
        from authentication.models import User
        
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        
        # Check if user already has member profile (only on create)
        if not self.instance and hasattr(user, 'member_profile'):
            raise serializers.ValidationError("This user already has a member profile.")
        
        return value
    
    def create(self, validated_data):
        """Create member profile"""
        from authentication.models import User
        
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        
        member = Member.objects.create(user=user, **validated_data)
        return member


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for attendance records"""
    
    member_name = serializers.CharField(source='member.user.get_full_name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'member', 'member_name', 'church_branch',
            'event_name', 'date', 'status', 'check_in_time',
            'check_out_time', 'duration', 'notes', 'recorded_by',
            'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']
    
    def validate(self, attrs):
        """Validate attendance data"""
        # Ensure check_out_time is after check_in_time
        check_in = attrs.get('check_in_time')
        check_out = attrs.get('check_out_time')
        
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({
                "check_out_time": "Check-out time must be after check-in time."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create attendance record"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['recorded_by'] = request.user
        return super().create(validated_data)


class AttendanceCreateBulkSerializer(serializers.Serializer):
    """Serializer for bulk attendance creation"""
    
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )
    church_branch_id = serializers.IntegerField(required=True)
    event_name = serializers.CharField(max_length=200, required=True)
    date = serializers.DateField(required=True)
    status = serializers.ChoiceField(
        choices=Attendance.AttendanceStatus.choices,
        default=Attendance.AttendanceStatus.PRESENT
    )
    
    def validate_member_ids(self, value):
        """Validate all member IDs exist"""
        existing_ids = Member.objects.filter(id__in=value).values_list('id', flat=True)
        if len(existing_ids) != len(value):
            raise serializers.ValidationError("Some member IDs do not exist.")
        return value
    
    def create(self, validated_data):
        """Create multiple attendance records"""
        request = self.context.get('request')
        member_ids = validated_data.pop('member_ids')
        
        attendances = []
        for member_id in member_ids:
            attendance = Attendance(
                member_id=member_id,
                recorded_by=request.user if request else None,
                **validated_data
            )
            attendances.append(attendance)
        
        # Bulk create (ignore duplicates)
        created = Attendance.objects.bulk_create(
            attendances,
            ignore_conflicts=True
        )
        
        return created


class MemberNoteSerializer(serializers.ModelSerializer):
    """Serializer for member notes"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = MemberNote
        fields = [
            'id', 'member', 'title', 'content', 'is_confidential',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create note with current user as creator"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class MemberStatisticsSerializer(serializers.Serializer):
    """Serializer for member statistics"""
    
    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    inactive_members = serializers.IntegerField()
    new_members_this_month = serializers.IntegerField()
    new_members_this_year = serializers.IntegerField()
    members_by_status = serializers.DictField()
    members_by_gender = serializers.DictField()
    members_by_marital_status = serializers.DictField()
    average_age = serializers.FloatField()
    attendance_rate = serializers.FloatField()