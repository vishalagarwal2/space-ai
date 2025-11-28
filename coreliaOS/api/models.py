from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# Import business models
from .business_models import Business, BusinessProfile

class BusinessBrand(models.Model):
    """
    Model for storing business brand information
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_brand')
    company_name = models.CharField(max_length=255)
    logo_url = models.URLField(max_length=1000, blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#3b82f6')
    secondary_color = models.CharField(max_length=7, default='#10b981')
    font_family = models.CharField(max_length=100, default='Roboto')
    brand_voice = models.TextField(blank=True)
    industry = models.CharField(max_length=100, blank=True)
    target_audience = models.TextField(blank=True)
    business_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_business_brand'

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"


class SocialMediaPost(models.Model):
    """
    Model for storing social media post drafts and published posts
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('generating', 'Generating'),
        ('ready', 'Ready to Post'),
        ('refining', 'Refining'),
        ('publishing', 'Publishing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]
    
    # Support both admin users (Django User) and business users (Business model)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_media_posts', null=True, blank=True)
    business_id = models.UUIDField(null=True, blank=True, help_text="Business user ID for business-created posts")
    
    conversation = models.ForeignKey('knowledge_base.Conversation', on_delete=models.CASCADE, null=True, blank=True)
    business_profile = models.ForeignKey(BusinessBrand, on_delete=models.CASCADE, related_name='social_media_posts', null=True, blank=True)
    
    # Post type
    POST_TYPE_CHOICES = [
        ('single', 'Single Post'),
        ('carousel', 'Carousel Post'),
    ]
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='single', help_text="Type of post (single or carousel)")
    
    # Content
    post_type = models.CharField(max_length=20, choices=[('single', 'Single Post'), ('carousel', 'Carousel Post')], default='single', help_text="Type of post: single image or carousel")
    image_prompt = models.TextField(help_text="Prompt used to generate the image", blank=True)
    layout_json = models.TextField(blank=True, null=True, help_text="JSON layout for programmatic rendering")
    carousel_layouts = models.JSONField(default=list, help_text="Array of layout JSONs for carousel slides")
    generated_image_url = models.URLField(max_length=1000, blank=True, null=True, help_text="S3 URL of generated image")
    caption = models.TextField(help_text="Post caption")
    hashtags = models.TextField(help_text="Post hashtags")
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    user_input = models.TextField(help_text="Original user request")
    
    # Instagram integration
    instagram_post_id = models.CharField(max_length=100, blank=True, null=True)
    connected_account = models.ForeignKey('knowledge_base.ConnectedAccount', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_social_media_post'
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(business_id__isnull=False),
                name='api_social_media_post_user_or_business_required'
            )
        ]
    
    def __str__(self):
        if self.user:
            return f"Social Media Post {self.id} - {self.user.username} ({self.status})"
        else:
            return f"Social Media Post {self.id} - Business {self.business_id} ({self.status})"


class InstagramPost(models.Model):
    """
    Model for storing Instagram post information
    """
    POST_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('posted', 'Posted'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='instagram_posts')
    caption = models.TextField(blank=True)
    media_url = models.URLField(max_length=1000, blank=True, null=True)
    media_type = models.CharField(max_length=20, choices=[('image', 'Image'), ('video', 'Video')], default='image')
    status = models.CharField(max_length=20, choices=POST_STATUS_CHOICES, default='draft')
    instagram_post_id = models.CharField(max_length=255, blank=True, null=True)  # Instagram's post ID after posting
    scheduled_at = models.DateTimeField(blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_instagram_post'
        ordering = ['-created_at']

    def __str__(self):
        return f"Instagram Post {self.id} - {self.user.username} ({self.status})"


class ContentCalendar(models.Model):
    """Content calendar for organizing social media posts"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Support both admin users (Django User) and business users (Business model)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_calendars', null=True, blank=True)
    business_id = models.UUIDField(null=True, blank=True, help_text="Business user ID for business-created calendars")
    
    # Business profile identifier (can be a mock profile ID like "tailwind-financial" or a real BusinessBrand ID)
    business_profile_id = models.CharField(max_length=100, help_text="Business profile identifier")
    
    # Calendar metadata
    title = models.CharField(max_length=255, help_text="Calendar title (e.g., 'December 2024')")
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    
    # Business context (kept for backward compatibility and snapshot purposes)
    business_profile_data = models.JSONField(default=dict, help_text="Snapshot of business profile data used for generation")
    
    # Generation metadata
    generation_prompt = models.TextField(help_text="The prompt used to generate this calendar")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'api_content_calendar'
        ordering = ['-year', '-month', '-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(business_id__isnull=False),
                name='content_calendar_user_or_business_required'
            )
        ]
    
    def __str__(self):
        if self.user:
            return f"{self.title} - {self.business_profile_id} (Admin: {self.user.username})"
        else:
            return f"{self.title} - {self.business_profile_id} (Business: {self.business_id})"
    
    @property
    def owner_identifier(self):
        """Get a unique identifier for the calendar owner"""
        return f"user_{self.user.id}" if self.user else f"business_{self.business_id}"


class ContentIdea(models.Model):
    """Individual content ideas within a content calendar"""
    
    CONTENT_TYPE_CHOICES = [
        ('promo', 'Promotional'),
        ('educational', 'Educational'),
        ('behind_scenes', 'Behind the Scenes'),
        ('testimonial', 'Testimonial'),
        ('holiday', 'Holiday'),
    ]
    
    STATUS_CHOICES = [
        ('pending_approval', 'Needs Approval'),
        ('scheduled', 'Scheduled to Post'),
        ('published', 'Published'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_calendar = models.ForeignKey(ContentCalendar, on_delete=models.CASCADE, related_name='content_ideas')
    
    # Content details
    title = models.CharField(max_length=255, help_text="Short title/topic of the content idea")
    description = models.TextField(help_text="Detailed description of the content idea")
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES)
    
    # Post format
    POST_FORMAT_CHOICES = [
        ('single', 'Single Post'),
        ('carousel', 'Carousel Post'),
    ]
    post_format = models.CharField(max_length=20, choices=POST_FORMAT_CHOICES, default='single', help_text="Format of the post (single or carousel)")
    
    # LLM prompt to generate the actual post
    generation_prompt = models.TextField(help_text="The prompt to feed into the post generation endpoint")
    
    # Scheduling
    scheduled_date = models.DateField(help_text="Planned date for this post")
    scheduled_time = models.TimeField(null=True, blank=True, help_text="Planned time for this post")
    
    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending_approval')
    
    # Generated post reference (if already generated)
    generated_post = models.ForeignKey(SocialMediaPost, on_delete=models.SET_NULL, null=True, blank=True, help_text="Reference to generated social media post")
    published_post_id = models.CharField(max_length=255, blank=True, help_text="Platform-specific post ID after publishing")
    
    # Template selection (persisted to maintain consistency across sessions)
    selected_template = models.CharField(max_length=100, blank=True, null=True, help_text="Selected template ID for post generation")
    
    # User notes and media
    user_notes = models.TextField(blank=True, help_text="Additional notes from the user")
    media_urls = models.JSONField(default=list, help_text="URLs of user-provided images/videos for this post")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'api_content_idea'
        ordering = ['scheduled_date', 'scheduled_time', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_date} ({self.status})"
    
    def mark_scheduled(self):
        """Mark this content idea as scheduled"""
        self.status = 'scheduled'
        self.save()
    
    def mark_published(self, post_id):
        """Mark this content idea as published"""
        self.status = 'published'
        self.published_post_id = post_id
        self.published_at = timezone.now()
        self.save()
