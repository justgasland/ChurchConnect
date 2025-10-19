"""
Serializers for Denomination and Church Branch Management
"""

from rest_framework import serializers
from .models import Denomination, ChurchBranch, BranchDepartment
from  authentication.serializers import UserSerializer


class DenominationListSerializer(serializers.ModelSerializer):
    """Serializer for listing denominations (lightweight)"""
    
    total_branches = serializers.ReadOnlyField()
    total_members = serializers.ReadOnlyField()
    
    class Meta:
        model = Denomination
        fields = [
            'id', 'name', 'slug', 'logo', 'status',
            'total_branches', 'total_members', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class DenominationSerializer(serializers.ModelSerializer):
    """Full serializer for denomination details"""
    
    created_by = UserSerializer(read_only=True)
    total_branches = serializers.ReadOnlyField()
    total_members = serializers.ReadOnlyField()
    
    class Meta:
        model = Denomination
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 'cover_image',
            'headquarters', 'contact_email', 'contact_phone', 'website',
            'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url',
            'status', 'allow_public_registration', 'created_by',
            'total_branches', 'total_members', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_by', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Ensure denomination name is unique"""
        instance = self.instance
        if instance:
            # Check if name changed and if new name exists
            if instance.name != value and Denomination.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError("A denomination with this name already exists.")
        else:
            # Creating new denomination
            if Denomination.objects.filter(name__iexact=value).exists():
                raise serializers.ValidationError("A denomination with this name already exists.")
        return value
    
    def create(self, validated_data):
        """Create denomination with current user as creator"""
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class DenominationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating denominations"""
    
    class Meta:
        model = Denomination
        fields = [
            'name', 'description', 'logo', 'cover_image',
            'headquarters', 'contact_email', 'contact_phone', 'website',
            'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url',
            'allow_public_registration'
        ]


class BranchDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for church departments"""
    
    head = UserSerializer(read_only=True)
    head_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = BranchDepartment
        fields = [
            'id', 'name', 'description', 'head', 'head_id',
            'contact_email', 'contact_phone', 'is_active',
            'member_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChurchBranchListSerializer(serializers.ModelSerializer):
    """Serializer for listing church branches (lightweight)"""
    
    denomination_name = serializers.CharField(source='denomination.name', read_only=True)
    admin_name = serializers.CharField(source='admin_user.get_full_name', read_only=True)
    total_members = serializers.ReadOnlyField()
    
    class Meta:
        model = ChurchBranch
        fields = [
            'id', 'name', 'slug', 'denomination', 'denomination_name',
            'city', 'state', 'country', 'image', 'status',
            'admin_user', 'admin_name', 'total_members', 'created_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at']


class ChurchBranchSerializer(serializers.ModelSerializer):
    """Full serializer for church branch details"""
    
    denomination = DenominationListSerializer(read_only=True)
    denomination_id = serializers.IntegerField(write_only=True)
    admin_user_detail = UserSerializer(source='admin_user', read_only=True)
    departments = BranchDepartmentSerializer(many=True, read_only=True)
    
    full_address = serializers.ReadOnlyField()
    total_members = serializers.ReadOnlyField()
    google_maps_url = serializers.ReadOnlyField()
    
    class Meta:
        model = ChurchBranch
        fields = [
            'id', 'denomination', 'denomination_id', 'name', 'slug',
            'description', 'image', 'address', 'city', 'state',
            'country', 'postal_code', 'latitude', 'longitude',
            'full_address', 'google_maps_url', 'contact_email',
            'contact_phone', 'alternative_phone', 'admin_user',
            'admin_user_detail', 'status', 'service_times',
            'seating_capacity', 'is_headquarters', 'allow_online_giving',
            'allow_event_registration', 'established_date',
            'departments', 'total_members', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def validate_denomination_id(self, value):
        """Validate denomination exists"""
        try:
            Denomination.objects.get(id=value)
        except Denomination.DoesNotExist:
            raise serializers.ValidationError("Denomination does not exist.")
        return value
    
    def validate(self, attrs):
        """Custom validation"""
        # Ensure at least one contact method
        if not attrs.get('contact_email') and not attrs.get('contact_phone'):
            raise serializers.ValidationError(
                "Either contact email or contact phone must be provided."
            )
        
        # Validate coordinates if provided
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        if (latitude and not longitude) or (longitude and not latitude):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )
        
        return attrs


class ChurchBranchCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating church branches"""
    
    class Meta:
        model = ChurchBranch
        fields = [
            'denomination', 'name', 'description', 'image',
            'address', 'city', 'state', 'country', 'postal_code',
            'latitude', 'longitude', 'contact_email', 'contact_phone',
            'alternative_phone', 'admin_user', 'service_times',
            'seating_capacity', 'is_headquarters', 'allow_online_giving',
            'allow_event_registration', 'established_date'
        ]
    
    def validate(self, attrs):
        """Validate branch data"""
        # Check if admin user belongs to the same denomination
        admin_user = attrs.get('admin_user')
        denomination = attrs.get('denomination')
        
        if admin_user and denomination:
            # Admin should ideally belong to the same denomination
            if admin_user.denomination and admin_user.denomination != denomination:
                raise serializers.ValidationError({
                    "admin_user": "Admin user should belong to the same denomination."
                })
        
        return attrs