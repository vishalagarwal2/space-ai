from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid

class Business(models.Model):
    """
    Model for storing business user accounts (separate from Django's User model)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Hashed password
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'api_business'
        verbose_name = 'Business User'
        verbose_name_plural = 'Business Users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def set_password(self, raw_password):
        """Hash and set the password"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash"""
        return check_password(raw_password, self.password)


class BusinessProfile(models.Model):
    """
    Model for storing detailed business profile information
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name='profile')
    
    # Basic Information
    business_name = models.CharField(max_length=255, blank=True)
    website_url = models.URLField(max_length=500, blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    
    # Branding
    logo_url = models.URLField(max_length=1000, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#3B82F6')
    secondary_color = models.CharField(max_length=7, default='#10B981')
    accent_color = models.CharField(max_length=7, default='#F59E0B', blank=True)
    font_family = models.CharField(max_length=100, blank=True)
    
    # Brand Details
    brand_mission = models.TextField(blank=True)
    brand_values = models.TextField(blank=True)
    business_basic_details = models.TextField(blank=True)
    business_services = models.TextField(blank=True)
    business_additional_details = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_business_profile'
        verbose_name = 'Business Profile'
        verbose_name_plural = 'Business Profiles'
    
    def __str__(self):
        return f"{self.business_name or 'Unnamed Business'} - {self.business.email}"
    
    def to_dict(self):
        """Convert profile to dictionary for API responses"""
        return {
            'id': str(self.id),
            'business_id': str(self.business.id),
            'business_name': self.business_name,
            'website_url': self.website_url,
            'instagram_handle': self.instagram_handle,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'font_family': self.font_family,
            'brand_mission': self.brand_mission,
            'brand_values': self.brand_values,
            'business_basic_details': self.business_basic_details,
            'business_services': self.business_services,
            'business_additional_details': self.business_additional_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

