from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from knowledge_base.models import KnowledgeBaseConfig
from coreliaOS.decorators import login_required
import json
import asyncio
import os
from functools import wraps



def async_require_GET(view_func):
    async def _wrapped_view(request, *args, **kwargs):
        if request.method != "GET":
            return JsonResponse({"error": "Method not allowed"}, status=405)
        return await view_func(request, *args, **kwargs)
    return _wrapped_view

@require_http_methods(["GET"])
def public_api(request):
    """Public API endpoint - accessible to everyone"""
    return JsonResponse({
        'message': 'This is a public API endpoint',
        'status': 'success',
        'data': {
            'timestamp': '2025-01-01T00:00:00Z',
            'version': '1.0.0'
        }
    })

@async_require_GET
async def public_async_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    """Public Async API endpoint - accessible to everyone"""
    await asyncio.sleep(1)  # Simulate async work
    return JsonResponse({
        'message': 'This is a public API endpoint',
        'status': 'success',
        'data': {
            'timestamp': '2025-01-01T00:00:00Z',
            'version': '1.0.0'
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    """Login API endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({
                'error': 'Username and password are required',
                'status': 'error'
            }, status=400)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Force session save to ensure cookies are set
            request.session.save()
            
            response = JsonResponse({
                'message': 'Login successful',
                'status': 'success',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }
            })
            
            # Log session info for debugging
            import logging
            from django.conf import settings
            logger = logging.getLogger(__name__)
            logger.warning(f"Session saved: {request.session.session_key}")
            logger.warning(f"Session age: {request.session.get_expiry_age()}")
            logger.warning(f"Response will have cookie headers")
            
            # Debug: Log what cookies will be sent
            logger.warning(f"Session cookie settings: Samesite={settings.SESSION_COOKIE_SAMESITE}, Secure={settings.SESSION_COOKIE_SECURE}")
            
            return response
        else:
            return JsonResponse({
                'error': 'Invalid credentials',
                'status': 'error'
            }, status=401)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'status': 'error'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_api(request):
    """User registration API endpoint"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        # Validation
        if not username or not email or not password:
            return JsonResponse({
                'error': 'Username, email, and password are required',
                'status': 'error'
            }, status=400)
        
        # Validate email
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'error': 'Invalid email format',
                'status': 'error'
            }, status=400)
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'error': 'Username already exists',
                'status': 'error'
            }, status=400)
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'error': 'Email already registered',
                'status': 'error'
            }, status=400)
        
        # Use database transaction to ensure atomicity
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create knowledge base config as part of setup process
            try:
                KnowledgeBaseConfig.objects.create(
                    user=user,
                    default_embedding_model="openai_ada",
                    default_vector_store="pinecone",
                    default_chunk_size=1000,
                    default_chunk_overlap=200,
                    document_retention_days=365,
                    conversation_retention_days=90,
                    default_similarity_threshold=0.2,
                    max_search_results=20,
                    sync_notifications=True,
                    error_notifications=True
                    # Note: API keys are now always read from environment variables, not stored in database
                )
            except Exception as config_error:
                logging.error(f"Failed to create KnowledgeBaseConfig: {str(config_error)}")
                # The transaction will be rolled back automatically
                raise config_error
        
        # Auto-login after successful registration
        login(request, user)
        
        return JsonResponse({
            'message': 'User registered successfully',
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=201)
    
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in register_api: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Invalid JSON data',
            'status': 'error'
        }, status=400)
    except Exception as e:
        logging.error(f"Exception in register_api: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({
            'error': 'Registration failed. Please try again.',
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_api(request):
    """Logout API endpoint"""
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({
            'message': 'Logout successful',
            'status': 'success'
        })
    else:
        return JsonResponse({
            'error': 'User not authenticated',
            'status': 'error'
        }, status=401)


@login_required
@require_http_methods(["GET"])
def protected_api(request):
    """Protected API endpoint - requires authentication"""
    return JsonResponse({
        'message': 'This is a protected API endpoint',
        'status': 'success',
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'date_joined': request.user.date_joined.isoformat(),
        },
        'data': {
            'secret_message': 'Only authenticated users can see this!',
            'user_permissions': list(request.user.get_all_permissions()),
        }
    })


@login_required
@require_http_methods(["GET"])
def user_profile_api(request):
    """Get current user's profile"""
    return JsonResponse({
        'message': 'User profile retrieved successfully',
        'status': 'success',
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'date_joined': request.user.date_joined.isoformat(),
            'last_login': request.user.last_login.isoformat() if request.user.last_login else None,
        }
    })


@login_required
@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def update_profile_api(request):
    """Update current user's profile"""
    try:
        data = json.loads(request.body)
        user = request.user
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Validate email
            try:
                validate_email(data['email'])
                # Check if email already exists for another user
                if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                    return JsonResponse({
                        'error': 'Email already registered by another user',
                        'status': 'error'
                    }, status=400)
                user.email = data['email']
            except ValidationError:
                return JsonResponse({
                    'error': 'Invalid email format',
                    'status': 'error'
                }, status=400)
        
        user.save()
        
        return JsonResponse({
            'message': 'Profile updated successfully',
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON data',
            'status': 'error'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def admin_only_api(request):
    """Admin-only API endpoint"""
    if not request.user.is_staff:
        return JsonResponse({
            'error': 'Admin access required',
            'status': 'error'
        }, status=403)
    
    # Get all users (admin only)
    users = User.objects.all()
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        })
    
    return JsonResponse({
        'message': 'Admin data retrieved successfully',
        'status': 'success',
        'data': {
            'total_users': users.count(),
            'users': users_data
        }
    })


@require_http_methods(["GET"])
def auth_status_api(request):
    """Check authentication status"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'status': 'success',
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_staff': request.user.is_staff,
                'is_superuser': request.user.is_superuser,
            }
        })
    else:
        return JsonResponse({
            'authenticated': False,
            'status': 'success',
            'message': 'User not authenticated'
        })
    

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import storage
from googleapiclient.errors import HttpError
import json
import os
from django.conf import settings
import logging
import traceback

class CompanyProfileAPIView(APIView):
    def post(self, request):
        try:
            # Extract form data
            gst_number = request.data.get('gstNumber')
            cin_number = request.data.get('cinNumber')
            pan_number = request.data.get('panNumber')
            primary_color = request.data.get('primaryColor')
            secondary_color = request.data.get('secondaryColor')
            font_family = request.data.get('fontFamily')
            company_logo = request.FILES.get('companyLogo')

            # Validate required fields
            if not all([gst_number, cin_number, pan_number, primary_color, secondary_color, font_family, company_logo]):
                return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Initialize Google Cloud Storage client
            credentials_dict = json.loads(getattr(settings, "GCS_CREDENTIALS", None))
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/devstorage.read_write']
            )
            storage_client = storage.Client(credentials=credentials, project=credentials_dict['project_id'])
            bucket_name = getattr(settings, "COMPANY_DATA_GCS_BUCKET", None)
            bucket = storage_client.bucket(bucket_name)

            # Upload logo to GCS
            logo_file_name = f"company_data/{company_logo.name}"
            blob = bucket.blob(logo_file_name)
            blob.upload_from_file(company_logo, content_type=company_logo.content_type)
            logo_url = f"https://storage.googleapis.com/{bucket_name}/{logo_file_name}"

            # Initialize Google Sheets client
            sheets_credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            sheets_service = build('sheets', 'v4', credentials=sheets_credentials)

            # Define spreadsheet ID and range
            spreadsheet_id =  os.getenv('SPREADSHEET_ID')
            range_name = 'Sheet1!A1:G1'

            # Prepare data for Google Sheets
            values = [[
                gst_number,
                cin_number,
                pan_number,
                primary_color,
                secondary_color,
                font_family,
                logo_url
            ]]
            body = {'values': values}

            # Append data to Google Sheet
            sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()

            return Response({"message": "Company profile saved successfully", "logo_url": logo_url}, status=status.HTTP_201_CREATED)

        except HttpError as e:
            return Response({"error": f"Google Sheets API error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Helper function for content calendar
def model_to_dict(instance, fields=None, exclude=None):
    """Convert model instance to dictionary"""
    from .serializers import SocialMediaPostSerializer
    
    data = {}
    opts = instance._meta
    
    for field in opts.concrete_fields:
        if fields and field.name not in fields:
            continue
        if exclude and field.name in exclude:
            continue
            
        value = field.value_from_object(instance)
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif isinstance(value, bytes):
            value = value.decode('utf-8')
        data[field.name] = value
    
    # Special handling for ContentIdea to include generated_post data
    if hasattr(instance, 'generated_post') and instance.generated_post:
        try:
            data['generated_post_data'] = SocialMediaPostSerializer.to_dict(instance.generated_post)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Error serializing generated_post: {str(e)}")
    
    return data


# Content Calendar API Endpoints
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def generate_content_calendar(request):
    """Generate a content calendar using LLM"""
    try:
        from .models import ContentCalendar, ContentIdea
        from openai import OpenAI
        from datetime import datetime, date
        from dateutil.relativedelta import relativedelta
        import calendar as cal_module
        import logging
        
        logger = logging.getLogger(__name__)
        
        data = json.loads(request.body)
        
        # Get business profile data from request
        business_profile = data.get('business_profile', {})
        business_profile_id = data.get('business_profile_id')
        
        if not business_profile:
            return JsonResponse({
                'success': False,
                'error': 'Business profile data is required'
            }, status=400)
        
        # We always expect a business_profile_id for mock profiles
        if not business_profile_id:
            return JsonResponse({
                'success': False,
                'error': 'Business profile ID is required'
            }, status=400)
        
        # Get current date and calculate next month
        today = date.today()
        next_month_date = today + relativedelta(months=1)
        target_month = next_month_date.month
        target_year = next_month_date.year
        month_name = cal_module.month_name[target_month]
        
        # Delete any existing calendar for this user/business_profile_id/month/year before creating a new one
        # This allows users to regenerate calendars
        
        # Determine filter based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            filter_kwargs = {
                'business_id': business_id,
                'business_profile_id': business_profile_id,
                'month': target_month,
                'year': target_year
            }
        else:
            # For admin users, use Django user
            filter_kwargs = {
                'user': request.user,
                'business_profile_id': business_profile_id,
                'month': target_month,
                'year': target_year
            }
            
        existing_calendars = ContentCalendar.objects.filter(**filter_kwargs)
        if existing_calendars.exists():
            logger.info(f"Deleting {existing_calendars.count()} existing calendar(s) for {month_name} {target_year} before generating new one")
            existing_calendars.delete()
        
        # Build the generation prompt
        website_url = business_profile.get('website_url', '')
        instagram_handle = business_profile.get('instagram_handle', '')
        company_name = business_profile.get('company_name', business_profile.get('name', ''))
        industry = business_profile.get('industry', '')
        brand_mission = business_profile.get('brand_mission', '')
        brand_values = business_profile.get('brand_values', '')
        tagline = business_profile.get('tagline', '')
        business_basic_details = business_profile.get('business_basic_details', '')
        business_services = business_profile.get('business_services', '')
        business_context = business_profile.get('business_context', '')
        business_additional_details = business_profile.get('business_additional_details', '')
        
        # Build business details section
        business_details_section = ""
        if business_basic_details:
            business_details_section += f"\n- Business Overview: {business_basic_details}"
        if business_services:
            business_details_section += f"\n- Services/Offerings: {business_services}"
        if business_context:
            business_details_section += f"\n- Business Context: {business_context}"
        if business_additional_details:
            business_details_section += f"\n- Additional Details: {business_additional_details}"
        
        # Determine if this is vehicle recycling specific based on business details
        is_vehicle_recycling = (
            'vehicle' in business_basic_details.lower() or 
            'vehicle' in business_services.lower() or
            'scrap' in business_services.lower() or
            'vehicle' in business_context.lower()
        )
        
        vehicle_specific_instruction = ""
        if is_vehicle_recycling:
            vehicle_specific_instruction = """
CRITICAL: This business specializes in VEHICLE RECYCLING and END-OF-LIFE VEHICLE PROCESSING. 
- ALL content ideas MUST be specifically about vehicles, car scrapping, vehicle recycling, or related automotive topics
- DO NOT create generic recycling or sustainability content
- Focus on: old vehicles, car scrapping services, vehicle disposal, saving money on new vehicles through scrapping, India's Vehicle Scrapping Policy, etc.
- The business helps people scrap their old vehicles and save money on their next purchase
"""
        
        generation_prompt = f"""Generate 5 content ideas for {company_name}'s Instagram over {month_name} {target_year}, while incorporating the brand's mission and values.

Business Context:
- Company: {company_name}
- Industry: {industry}
- Tagline: {tagline}
- Brand Mission: {brand_mission}
- Brand Values: {brand_values}
- Website: {website_url}
- Instagram: {instagram_handle}{business_details_section}
{vehicle_specific_instruction}
Requirements:
- Generate exactly 5 content ideas
- Content mix: 2 promotional posts, 3 informational/educational posts
- Spread posts across the month (dates should be realistic for {month_name} {target_year})
- Each idea should be specific, actionable, and aligned with the brand
- Content MUST be directly relevant to the business's specific services and offerings mentioned above
- For each content idea, provide:
  1. A catchy title (max 60 characters)
  2. A detailed description - ENHANCED FOR EDUCATIONAL CONTENT:
     * For educational posts: Provide 4-5 sentences with substantial, informative content that can be used to generate detailed carousel slides or comprehensive single posts
     * For other content types: 2-3 sentences explaining the content
  3. The content type (promo, educational, user_generated, behind_scenes, testimonial, or holiday)
  4. A specific date in {month_name} {target_year}
  5. An LLM prompt that can be used to generate the actual Instagram post
  6. Post format (single or carousel) - Educational content should prefer carousel format for better information delivery

CRITICAL: For the generation_prompt (field 5), follow this exact format:
- Structure it as: "Create a [post type] post for [business] with '[MAIN SLOGAN]' as the main slogan. Include '[OFFER/DETAIL 1]' as [context]. Also include line '[SUPPORTING LINE]'."
- Focus on 1 main slogan (bold, center attention) + max 2-3 short supporting lines
- Do NOT include hashtag instructions - hashtags are handled separately
- Keep supporting text short and punchy
- Always specify the main slogan in quotes for emphasis

Return ONLY a valid JSON array with 5 objects, each having these exact fields:
- title: string
- description: string (enhanced for educational content as specified above)
- content_type: string (one of: promo, educational, behind_scenes, testimonial, holiday)
- scheduled_date: string (YYYY-MM-DD format)
- generation_prompt: string (the prompt to use for generating the actual post)
- post_format: string (either "single" or "carousel" - use "carousel" for educational content with multiple points to cover)

Example format:
[
  {{
    "title": "Scrap Your Old Car, Save on New Ride!",
    "description": "Promote the vehicle scrapping service highlighting how customers can save up to ₹1,00,000 on their next vehicle purchase by scrapping their old car. Include information about the streamlined process and environmental benefits.",
    "content_type": "promo",
    "scheduled_date": "2024-12-07",
    "generation_prompt": "Create a promotional post for vehicle recycling with 'Scrap. Save. Smile.' as the main slogan. Include 'Upto ₹75,000 Road Tax Rebate' as a special offer. Also include line 'Scrapping to Unlock 25% Off your next ride'.",
    "post_format": "single"
  }},
  {{
    "title": "Complete Guide to Vehicle Scrapping Process",
    "description": "Educational carousel explaining the step-by-step vehicle scrapping process in India. Cover documentation requirements, eligibility criteria, environmental benefits, and financial incentives. Explain how the Vehicle Scrapping Policy works and what customers need to know before scrapping their old vehicles. Include information about authorized scrapping centers and the certificate process.",
    "content_type": "educational",
    "scheduled_date": "2024-12-10",
    "generation_prompt": "Create an educational carousel post about vehicle scrapping process with 'Know Your Scrapping Rights' as the main theme. Cover documentation, eligibility, benefits, and process steps across multiple slides.",
    "post_format": "carousel"
  }}
]

Important: Return ONLY the JSON array, no other text or explanation."""
        
        # Call OpenAI API
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Use cheaper model by default (gpt-4o-mini is much cheaper than gpt-4)
        # Can be overridden via CONTENT_CALENDAR_MODEL environment variable
        model = os.getenv('CONTENT_CALENDAR_MODEL', 'gpt-4o-mini')
        
        logger.info(f"Generating content calendar for {company_name} - {month_name} {target_year} using {model}")
        
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional social media strategist. You create detailed content calendars for businesses. Always return valid JSON arrays with exactly the requested structure."
                },
                {
                    "role": "user",
                    "content": generation_prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_content = completion.choices[0].message.content.strip()
        logger.info(f"LLM Response: {response_content[:200]}...")
        
        # Parse the JSON response
        # Remove markdown code blocks if present
        if response_content.startswith('```json'):
            response_content = response_content[7:]
        if response_content.startswith('```'):
            response_content = response_content[3:]
        if response_content.endswith('```'):
            response_content = response_content[:-3]
        response_content = response_content.strip()
        
        content_ideas_data = json.loads(response_content)
        
        if not isinstance(content_ideas_data, list) or len(content_ideas_data) != 5:
            return JsonResponse({
                'success': False,
                'error': 'Invalid response format from LLM'
            }, status=500)
        
        # Create the content calendar with appropriate user/business_id
        create_kwargs = {
            'business_profile_id': business_profile_id,
            'title': f"{month_name} {target_year} - {company_name}",
            'month': target_month,
            'year': target_year,
            'business_profile_data': business_profile,
            'generation_prompt': generation_prompt
        }
        
        # Set user or business_id based on authentication type
        if request.session.get('user_type') == 'business':
            create_kwargs['business_id'] = request.session.get('business_id')
        else:
            create_kwargs['user'] = request.user
            
        content_calendar = ContentCalendar.objects.create(**create_kwargs)
        
        # Create content ideas
        created_ideas = []
        for idea_data in content_ideas_data:
            try:
                scheduled_date_str = idea_data['scheduled_date']
                scheduled_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
                
                # Determine post format: educational content should default to carousel
                post_format = idea_data.get('post_format', 'single')
                if idea_data['content_type'] == 'educational' and post_format == 'single':
                    post_format = 'carousel'  # Force educational content to be carousel
                
                content_idea = ContentIdea.objects.create(
                    content_calendar=content_calendar,
                    title=idea_data['title'],
                    description=idea_data['description'],
                    content_type=idea_data['content_type'],
                    post_format=post_format,
                    scheduled_date=scheduled_date,
                    generation_prompt=idea_data['generation_prompt'],
                    status='pending_approval'
                )
                
                created_ideas.append(model_to_dict(content_idea))
                logger.info(f"Created content idea: {content_idea.title}")
            except Exception as e:
                logger.error(f"Error creating content idea: {str(e)}")
                continue
        
        return JsonResponse({
            'success': True,
            'data': {
                'calendar': model_to_dict(content_calendar),
                'content_ideas': created_ideas
            },
            'message': f'Content calendar generated successfully for {month_name} {target_year}'
        })
        
    except json.JSONDecodeError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"JSON decode error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request or response'
        }, status=400)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating content calendar: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_content_calendars(request):
    """Get user's content calendars, optionally filtered by business profile"""
    try:
        from .models import ContentCalendar, ContentIdea
        from .serializers import ContentCalendarSerializer, ContentIdeaSerializer
        
        # Get business profile filter (required for mock profiles)
        business_profile_id = request.GET.get('business_profile_id')
        
        if not business_profile_id:
            return JsonResponse({
                'success': False,
                'error': 'Business profile ID is required'
            }, status=400)
        
        # Determine user based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            # For business users, filter by business_id
            filter_kwargs = {
                'business_id': business_id,
                'business_profile_id': business_profile_id
            }
        else:
            # For admin users, use Django user
            filter_kwargs = {
                'user': request.user,
                'business_profile_id': business_profile_id
            }
        
        calendars = ContentCalendar.objects.filter(**filter_kwargs).order_by('-year', '-month')
        
        calendars_data = []
        for calendar in calendars:
            calendar_dict = ContentCalendarSerializer.to_dict(calendar)
            # Add content ideas
            content_ideas = ContentIdea.objects.filter(content_calendar=calendar).order_by('scheduled_date')
            calendar_dict['content_ideas'] = [ContentIdeaSerializer.to_dict(idea) for idea in content_ideas]
            calendars_data.append(calendar_dict)
        
        return JsonResponse({
            'success': True,
            'data': {
                'calendars': calendars_data
            }
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting content calendars: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get content calendars'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def approve_content_idea(request, idea_id):
    """Mark a content idea as scheduled (legacy approve endpoint)"""
    try:
        from django.shortcuts import get_object_or_404
        from .models import ContentIdea
        
        # Determine filter based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__business_id=business_id
            )
        else:
            # For admin users, use Django user
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__user=request.user
            )
        
        content_idea.mark_scheduled()
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(content_idea),
            'message': 'Content idea marked as scheduled successfully'
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error marking content idea as scheduled: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to mark content idea as scheduled'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def unschedule_content_idea(request, idea_id):
    """Mark a content idea as pending approval (unschedule)"""
    try:
        from django.shortcuts import get_object_or_404
        from .models import ContentIdea
        
        # Determine filter based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__business_id=business_id
            )
        else:
            # For admin users, use Django user
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__user=request.user
            )
        
        # Change status back to pending_approval
        content_idea.status = 'pending_approval'
        content_idea.approved_at = None  # Clear the approval timestamp
        content_idea.save()
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(content_idea),
            'message': 'Content idea unscheduled successfully'
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error unscheduling content idea: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to unschedule content idea'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["PUT"])
def update_content_idea(request, idea_id):
    """Update a content idea"""
    try:
        from django.shortcuts import get_object_or_404
        from .models import ContentIdea
        from datetime import datetime
        
        # Determine filter based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__business_id=business_id
            )
        else:
            # For admin users, use Django user
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__user=request.user
            )
        
        data = json.loads(request.body)
        
        # Track if title or description changed to update generation_prompt
        title_changed = 'title' in data and data['title'] != content_idea.title
        description_changed = 'description' in data and data['description'] != content_idea.description
        
        # Update allowed fields
        updatable_fields = ['title', 'description', 'scheduled_date', 'scheduled_time', 'user_notes', 'status', 'selected_template', 'post_format']
        for field in updatable_fields:
            if field in data:
                if field == 'scheduled_date' and isinstance(data[field], str):
                    data[field] = datetime.strptime(data[field], '%Y-%m-%d').date()
                setattr(content_idea, field, data[field])
        
        # Update generation_prompt if title or description changed
        if title_changed or description_changed:
            # Create a new generation prompt based on updated title and description
            new_generation_prompt = f"Create a social media post about: {content_idea.title}\n\nDescription: {content_idea.description}"
            content_idea.generation_prompt = new_generation_prompt
        
        content_idea.save()
        
        return JsonResponse({
            'success': True,
            'data': model_to_dict(content_idea),
            'message': 'Content idea updated successfully'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating content idea: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to update content idea'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_content_calendar(request, calendar_id):
    """Delete a content calendar and all its content ideas"""
    try:
        from .models import ContentCalendar
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Determine filter based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            try:
                content_calendar = ContentCalendar.objects.get(
                    id=calendar_id,
                    business_id=business_id
                )
            except ContentCalendar.DoesNotExist:
                logger.warning(f"Content calendar {calendar_id} not found for business {business_id}")
                return JsonResponse({
                    'success': False,
                    'error': 'Content calendar not found'
                }, status=404)
        else:
            # For admin users, use Django user
            try:
                content_calendar = ContentCalendar.objects.get(
                    id=calendar_id,
                    user=request.user
                )
            except ContentCalendar.DoesNotExist:
                logger.warning(f"Content calendar {calendar_id} not found for user {request.user.username}")
                return JsonResponse({
                    'success': False,
                    'error': 'Content calendar not found'
                }, status=404)
        
        calendar_title = content_calendar.title
        content_calendar.delete()  # This will cascade delete all content ideas
        
        return JsonResponse({
            'success': True,
            'message': f'Content calendar "{calendar_title}" deleted successfully'
        })
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting content calendar: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Failed to delete content calendar: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def generate_post_for_content_idea(request, idea_id):
    """Generate a social media post for a content idea and link it"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        from django.shortcuts import get_object_or_404
        from .models import ContentIdea
        from .services import SocialMediaPostService
        from .serializers import SocialMediaPostSerializer
        
        # Determine filter based on authentication type
        if request.session.get('user_type') == 'business':
            # For business users, use business_id from session
            business_id = request.session.get('business_id')
            if not business_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Business authentication invalid'
                }, status=401)
            
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__business_id=business_id
            )
        else:
            # For admin users, use Django user
            content_idea = get_object_or_404(
                ContentIdea,
                id=idea_id,
                content_calendar__user=request.user
            )
        
        # Check if business profile data and template are provided in the request
        import json
        try:
            request_data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            request_data = {}
        
        provided_business_profile = request_data.get('business_profile')
        selected_template = request_data.get('selected_template')
        override_post_format = request_data.get('post_format')
        
        # For business users, always use the database profile; for admin users, use provided or fallback
        if request.session.get('user_type') == 'business':
            # Business users: get profile from database using business_id
            business_id = request.session.get('business_id')
            from .helpers import get_business_profile_by_business_id
            
            business_profile_data = get_business_profile_by_business_id(business_id)
            if not business_profile_data:
                return JsonResponse({
                    'success': False,
                    'error': f'Business profile not found for business ID: {business_id}'
                }, status=404)
            
            logger.info(f"📥 [Content Calendar Post Gen] Using database business profile: {business_profile_data.get('company_name')}, font: {business_profile_data.get('font_family')}")
        else:
            # Admin users: use provided profile or fallback to calendar data
            if provided_business_profile:
                logger.info(f"📥 [Content Calendar Post Gen] Using provided business profile: {provided_business_profile.get('company_name')}, font: {provided_business_profile.get('font_family', provided_business_profile.get('fontFamily', provided_business_profile.get('brandGuidelines', {}).get('fontFamily', 'N/A')))}")
                business_profile_data = provided_business_profile
            else:
                # Get business profile data from calendar as fallback
                business_profile_data = content_idea.content_calendar.business_profile_data or {}
                logger.info(f"📥 [Content Calendar Post Gen] Using stored calendar business profile (no provided profile)")
        
        # Generate the post using the generation prompt
        # For business users, we need to handle post generation differently since they don't have Django User objects
        if request.session.get('user_type') == 'business':
            # Business user flow - use SocialMediaPostService with business_id
            business_id = request.session.get('business_id')
            logger.info(f"📥 [Content Calendar Post Gen] Using provided business profile: {business_profile_data.get('company_name', 'Unknown')}, font: {business_profile_data.get('font_family', 'Unknown')}")
            
            response = SocialMediaPostService.generate_post(
                user=None,  # No Django user for business users
                user_input=content_idea.generation_prompt,
                conversation_id=None,  # Business users don't have conversations
                provided_business_profile=business_profile_data,
                business_id=business_id,
                content_idea=content_idea,
                override_post_format=override_post_format
            )
        else:
            # Admin user flow - use SocialMediaPostService with Django user
            response = SocialMediaPostService.generate_post(
                request.user,
                content_idea.generation_prompt,
                conversation_id=None,
                provided_business_profile=business_profile_data,
                content_idea=content_idea,
                override_post_format=override_post_format
            )
        
        # Parse the response and convert to content calendar format
        if hasattr(response, 'content'):
            import json
            response_data = json.loads(response.content)
            
            # Handle both content calendar format (success: boolean) and social media format (status: string)
            is_success = response_data.get('success') or response_data.get('status') == 'success'
            
            if is_success and response_data.get('data'):
                # Get the generated post ID
                post_id = response_data['data'].get('id')
                
                if post_id:
                    # Link the generated post to the content idea (both admin and business users)
                    from .models import SocialMediaPost
                    try:
                        # For business users, filter by business_id; for admin users, filter by user
                        if request.session.get('user_type') == 'business':
                            business_id = request.session.get('business_id')
                            generated_post = SocialMediaPost.objects.get(id=post_id, business_id=business_id)
                        else:
                            generated_post = SocialMediaPost.objects.get(id=post_id, user=request.user)
                        
                        # Delete old generated_post if it exists (for regeneration)
                        if content_idea.generated_post:
                            old_post = content_idea.generated_post
                            logger.info(f"Deleting old generated post {old_post.id} before linking new post {post_id}")
                            old_post.delete()
                        
                        # Link the new generated post to the content idea
                        content_idea.generated_post = generated_post
                        
                        # Sync post_format from generated post to content idea
                        # This ensures the ContentIdea always reflects what was actually generated
                        if generated_post.post_type:
                            old_format = content_idea.post_format
                            content_idea.post_format = generated_post.post_type
                            if old_format != generated_post.post_type:
                                logger.info(f"Updated post_format from '{old_format}' to '{generated_post.post_type}' for content idea {content_idea.id}")
                            else:
                                logger.info(f"Post format '{generated_post.post_type}' matches for content idea {content_idea.id}")
                        
                        # Store the selected template if provided
                        if selected_template:
                            content_idea.selected_template = selected_template
                            logger.info(f"Storing selected template {selected_template} for content idea {content_idea.id}")
                        
                        # Update status: if already published, keep as published, otherwise set to pending_approval
                        if content_idea.status != 'published':
                            content_idea.status = 'pending_approval'
                        
                        content_idea.save()
                        
                        logger.info(f"Successfully linked generated post {post_id} (type: {generated_post.post_type}) to content idea {content_idea.id} (format: {content_idea.post_format})")
                        
                    except SocialMediaPost.DoesNotExist:
                        logger.error(f"Generated post {post_id} not found in database")
                        return JsonResponse({
                            'success': False,
                            'error': 'Generated post not found'
                        }, status=404)
                
                # Convert social media post response to content calendar format for both user types
                service_response_data = json.loads(response.content)
                
                # Create unified content calendar format response
                unified_response = {
                    'success': service_response_data.get('status') == 'success',
                    'message': service_response_data.get('message', 'Post generated successfully'),
                    'data': {
                        'generated_post': service_response_data.get('data'),
                        'content_idea': model_to_dict(content_idea) if content_idea else None
                    }
                }
                
                return JsonResponse(unified_response, status=response.status_code)
        
        # If we get here, something went wrong
        return JsonResponse({
            'success': False,
            'error': 'Failed to generate post'
        }, status=500)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error generating post for content idea: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': f'Failed to generate post: {str(e)}'
        }, status=500)