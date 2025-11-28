# Connected Accounts Feature - Instagram Business Integration

## 🎯 Objective

Enable users to connect their business Instagram accounts to the platform, allowing for seamless content creation, scheduling, and posting directly through our AI-powered social media assistant.

## 📋 Feature Overview

### Core Functionality
- **Account Connection**: Users can link their Instagram Business accounts via OAuth 2.0
- **Permission Management**: Request and manage posting permissions
- **Account Management**: View, manage, and disconnect linked accounts
- **Secure Token Storage**: Encrypted storage of access tokens and refresh tokens
- **Posting Capabilities**: Direct posting to Instagram through our platform

### Supported Platforms
- **Phase 1**: Instagram Business Accounts (Instagram Graph API)
- **Phase 2**: LinkedIn Business Pages
- **Future**: Twitter, Facebook Pages, TikTok Business

## 🔧 Technical Architecture

### Backend Implementation (Django)

#### 1. Data Models

```python
# models.py
class ConnectedAccount(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connected_accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # Account Information
    account_id = models.CharField(max_length=255)  # Platform-specific account ID
    username = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True)
    profile_picture_url = models.URLField(blank=True)
    
    # Authentication Tokens (Encrypted)
    access_token = models.TextField()  # Encrypted
    refresh_token = models.TextField(blank=True)  # Encrypted
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Permissions & Scopes
    granted_scopes = models.JSONField(default=list)
    permissions = models.JSONField(default=dict)
    
    # Status & Metadata
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'platform', 'account_id']
        ordering = ['-created_at']

```

#### 2. API Endpoints

```python
# views.py
@csrf_exempt
@login_required
def initiate_instagram_connection(request):
    """Initiate Instagram OAuth flow"""
    
@csrf_exempt
@login_required  
def instagram_oauth_callback(request):
    """Handle Instagram OAuth callback"""
    
@login_required
def get_connected_accounts(request):
    """Get user's connected accounts"""
    
@csrf_exempt
@login_required
def disconnect_account(request, account_id):
    """Disconnect a specific account"""
    
@csrf_exempt
@login_required
def post_to_instagram(request):
    """Post content to Instagram"""
```

#### 3. Instagram Graph API Integration

```python
# instagram_api.py
class InstagramAPIClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def get_user_info(self):
        """Get Instagram user information"""
        
    def create_media_container(self, image_url, caption):
        """Create media container for posting"""
        
    def publish_media(self, container_id):
        """Publish the media container"""
        
    def refresh_access_token(self, refresh_token):
        """Refresh expired access token"""
```

### Frontend Implementation (Next.js)

#### 1. Connected Accounts Tab Component

```typescript
// components/ConnectedAccounts.tsx
interface ConnectedAccount {
  id: string;
  platform: 'instagram' | 'linkedin' | 'twitter';
  username: string;
  display_name: string;
  profile_picture_url: string;
  is_active: boolean;
  is_verified: boolean;
  last_sync_at: string;
}

export default function ConnectedAccounts() {
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Component logic here
}
```

#### 2. Instagram Connection Flow

```typescript
// lib/api/connectedAccounts.ts
export const initiateInstagramConnection = async () => {
  return axiosInstance.get('/api/connected-accounts/instagram/connect');
};

export const getConnectedAccounts = async () => {
  return axiosInstance.get('/api/connected-accounts/');
};

export const disconnectAccount = async (accountId: string) => {
  return axiosInstance.delete(`/api/connected-accounts/${accountId}/`);
};
```

## 🔐 Security Implementation

### 1. Token Encryption
```python
# utils/encryption.py
from cryptography.fernet import Fernet
import base64

class TokenEncryption:
    def __init__(self):
        self.key = settings.SECRET_KEY.encode()[:32]
        self.cipher = Fernet(base64.urlsafe_b64encode(self.key))
    
    def encrypt_token(self, token):
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token):
        return self.cipher.decrypt(encrypted_token.encode()).decode()
```

### 2. Permission Scopes
```python
# Instagram required permissions
INSTAGRAM_SCOPES = [
    'instagram_basic',
    'instagram_content_publish',
    'pages_show_list',
    'pages_read_engagement'
]
```

## 📱 User Flow

### 1. Connection Process
1. User navigates to "Connected Accounts" tab
2. Clicks "Connect Instagram Account"
3. Redirected to Instagram OAuth consent screen
4. User grants permissions
5. Redirected back to platform with success message
6. Account appears in connected accounts list

### 2. Account Management
1. View all connected accounts with status
2. See last sync time and verification status
3. Disconnect accounts if needed
4. Reconnect expired accounts

### 3. Posting Integration
1. Create content using AI assistant
2. Select connected Instagram account
3. Preview post before publishing
4. Publish directly to Instagram

## 🚀 Implementation Plan

### Phase 1: Backend Foundation (Week 1)
- [ ] Create ConnectedAccount model
- [ ] Set up Instagram Graph API credentials
- [ ] Implement OAuth 2.0 flow
- [ ] Create API endpoints
- [ ] Add token encryption
- [ ] Write unit tests

### Phase 2: Frontend Integration (Week 2)
- [ ] Create Connected Accounts tab
- [ ] Implement Instagram connection flow
- [ ] Add account management UI
- [ ] Handle OAuth callbacks
- [ ] Add loading states and error handling

### Phase 3: Posting Integration (Week 3)
- [ ] Integrate Instagram posting API
- [ ] Update social media chat to use connected accounts
- [ ] Implement error handling and retry logic

### Phase 4: Testing & Polish (Week 4)
- [ ] End-to-end testing
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] User acceptance testing

## 🔧 Instagram Graph API Setup

### 1. Facebook Developer Account Setup
1. Create Facebook Developer account
2. Create new app in Facebook Developers Console
3. Add Instagram Basic Display product
4. Configure OAuth redirect URIs
5. Get App ID and App Secret

### 2. Required Permissions
- `instagram_basic` - Access basic profile information
- `instagram_content_publish` - Publish content to Instagram
- `pages_show_list` - Access user's Facebook Pages
- `pages_read_engagement` - Read page engagement data

### 3. API Endpoints to Implement
- User info: `GET /{user-id}`
- Media creation: `POST /{user-id}/media`
- Media publishing: `POST /{media-id}/publish`

## 📊 Database Schema

```sql
-- Connected Accounts Table
CREATE TABLE connected_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER NOT NULL REFERENCES auth_user(id),
    platform VARCHAR(20) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    profile_picture_url TEXT,
    access_token TEXT NOT NULL, -- Encrypted
    refresh_token TEXT, -- Encrypted
    token_expires_at TIMESTAMP,
    granted_scopes JSONB DEFAULT '[]',
    permissions JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, platform, account_id)
);

```

## 🧪 Testing Strategy

### 1. Unit Tests
- Model validation tests
- API endpoint tests
- Encryption/decryption tests
- Instagram API client tests

### 2. Integration Tests
- OAuth flow testing
- Token refresh testing
- Posting functionality testing
- Error handling testing

### 3. Security Tests
- Token encryption validation
- Permission scope validation
- SQL injection prevention
- XSS prevention

## 📚 Documentation

### 1. API Documentation
- Endpoint specifications
- Request/response examples
- Error codes and handling
- Rate limiting information

### 2. User Documentation
- Connection process guide
- Account management instructions
- Troubleshooting common issues
- Privacy and security information

## 🔄 Future Enhancements

### Phase 2 Features
- LinkedIn Business Page integration
- Twitter API integration
- Facebook Page posting
- Content scheduling
- Analytics integration

### Advanced Features
- Multi-account posting
- Content templates
- Performance analytics
- Automated posting
- Content approval workflows

## 📞 Support & Maintenance

### Monitoring
- API rate limit monitoring
- Token expiration alerts
- Failed posting notifications
- Performance metrics

### Maintenance
- Regular token refresh
- API version updates
- Security patches
- Feature updates

---

## 🎯 Success Metrics

- **User Adoption**: % of users who connect Instagram accounts
- **Connection Success Rate**: % of successful OAuth flows
- **Posting Success Rate**: % of successful posts
- **User Engagement**: Frequency of account usage
- **Error Rates**: API error and failure rates

This comprehensive plan provides a solid foundation for implementing the Connected Accounts feature with Instagram Business integration, ensuring security, scalability, and user experience are prioritized throughout the development process.
