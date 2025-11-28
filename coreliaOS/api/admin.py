from django.contrib import admin
from django.utils.html import format_html
import json
from .models import BusinessBrand, SocialMediaPost, InstagramPost, ContentCalendar, ContentIdea


@admin.register(BusinessBrand)
class BusinessBrandAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'industry', 'created_at']
    search_fields = ['company_name', 'user__username', 'industry']
    list_filter = ['industry', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SocialMediaPost)
class SocialMediaPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'caption_preview', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'caption']
    readonly_fields = ['created_at', 'updated_at']
    
    def caption_preview(self, obj):
        return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption
    caption_preview.short_description = 'Caption Preview'


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'media_type', 'created_at']
    list_filter = ['status', 'media_type', 'created_at']
    search_fields = ['user__username', 'caption']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ContentCalendar)
class ContentCalendarAdmin(admin.ModelAdmin):
    """Admin interface for ContentCalendar model"""
    
    list_display = ['title', 'user', 'month', 'year', 'content_idea_count', 'created_at']
    list_filter = ['year', 'month', 'created_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'business_profile_data_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'title', 'month', 'year')
        }),
        ('Generation Details', {
            'fields': ('generation_prompt', 'business_profile_data_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def content_idea_count(self, obj):
        """Get content idea count for calendar"""
        return obj.content_ideas.count()
    content_idea_count.short_description = 'Ideas'
    
    def business_profile_data_display(self, obj):
        """Display business profile data in formatted way"""
        if obj.business_profile_data:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.business_profile_data, indent=2)
            )
        return "No business profile data"
    business_profile_data_display.short_description = 'Business Profile Data'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user')


@admin.register(ContentIdea)
class ContentIdeaAdmin(admin.ModelAdmin):
    """Admin interface for ContentIdea model"""
    
    list_display = [
        'title', 'content_calendar', 'content_type', 'scheduled_date', 
        'status', 'created_at'
    ]
    list_filter = ['status', 'content_type', 'scheduled_date', 'created_at']
    search_fields = ['title', 'description', 'content_calendar__title']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'approved_at', 
        'published_at', 'media_urls_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'content_calendar', 'title', 'description', 'content_type', 'status')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'scheduled_time')
        }),
        ('Generation', {
            'fields': ('generation_prompt',),
            'classes': ('collapse',)
        }),
        ('Post References', {
            'fields': ('generated_post', 'published_post_id')
        }),
        ('User Content', {
            'fields': ('user_notes', 'media_urls_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at', 'published_at')
        })
    )
    
    def media_urls_display(self, obj):
        """Display media URLs in formatted way"""
        if obj.media_urls:
            return format_html(
                '<pre>{}</pre>',
                json.dumps(obj.media_urls, indent=2)
            )
        return "No media URLs"
    media_urls_display.short_description = 'Media URLs'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('content_calendar', 'content_calendar__user')


# Custom admin actions for content calendar
@admin.action(description='Approve selected content ideas')
def approve_content_ideas(modeladmin, request, queryset):
    """Approve selected content ideas"""
    count = 0
    for idea in queryset:
        idea.approve()
        count += 1
    modeladmin.message_user(request, f'Approved {count} content ideas.')


@admin.action(description='Reject selected content ideas')
def reject_content_ideas(modeladmin, request, queryset):
    """Reject selected content ideas"""
    count = 0
    for idea in queryset:
        idea.reject()
        count += 1
    modeladmin.message_user(request, f'Rejected {count} content ideas.')


# Add actions to content idea admin
ContentIdeaAdmin.actions = [approve_content_ideas, reject_content_ideas]

