# Social Media Manager - Frontend Implementation

## Overview
This document outlines the frontend implementation of the Social Media Manager feature for the Lance application. The feature provides an Instagram-style interface for creating social media posts through an AI-powered chat interface.

## Components Implemented

### 1. SocialMediaManager Component
**Location**: `src/components/SocialMediaManager.tsx`

**Features**:
- Instagram-style gradient design
- Call-to-action button with Instagram branding
- Feature highlights (AI-Powered, Brand Consistent, Easy Publishing)
- Responsive design

**Props**:
- `onStartChat`: Function to trigger chat interface

### 2. SocialMediaChat Component
**Location**: `src/components/SocialMediaChat.tsx`

**Features**:
- Full-screen chat interface
- Message history with user/assistant roles
- Typing indicator for AI responses
- Instagram-style avatars and branding
- Auto-scroll to latest messages
- Responsive design

**Props**:
- `onBack`: Function to return to main dashboard

### 3. Dashboard Integration
**Location**: `src/app/dashboard/page.tsx`

**Changes**:
- Added state management for chat view
- Integrated SocialMediaManager component
- Added conditional rendering for chat interface
- Maintained existing dashboard functionality

## Design System

### Color Palette
- **Primary Gradient**: Instagram's signature gradient (#f09433 → #e6683c → #dc2743 → #cc2366 → #bc1888)
- **Background**: #f8fafc (light gray)
- **Text**: #1e293b (dark slate)
- **Secondary Text**: #64748b (slate)

### Typography
- **Headers**: 700 weight, gradient text for titles
- **Body**: 400 weight, readable line heights
- **Small Text**: 0.875rem for timestamps and subtitles

### Interactive Elements
- **Buttons**: Gradient backgrounds with hover effects
- **Cards**: White backgrounds with subtle shadows
- **Input Fields**: Rounded corners with focus states
- **Avatars**: Circular with gradient backgrounds

## User Flow

1. **Dashboard View**: User sees the main dashboard with welcome message
2. **Social Media Manager**: Instagram-style card with "Make an Instagram Post" button
3. **Chat Interface**: Clicking the button opens the full-screen chat
4. **Message Exchange**: User can type requests, AI responds with suggestions
5. **Back Navigation**: User can return to dashboard from chat

## Technical Implementation

### State Management
- `showSocialMediaChat`: Boolean to toggle between dashboard and chat views
- `messages`: Array of message objects with role, content, and timestamp
- `inputValue`: Current input field value
- `isLoading`: Boolean for AI response simulation

### Message Structure
```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}
```

### Responsive Design
- Mobile-first approach
- Flexible grid layouts
- Touch-friendly interactive elements
- Optimized for various screen sizes

## Future Enhancements

### Backend Integration
- Connect to actual AI API endpoints
- Implement real-time message streaming
- Add user authentication for chat sessions
- Store conversation history

### Advanced Features
- Image generation and preview
- Post scheduling
- Brand consistency checking
- Analytics and insights
- Multi-platform support

### UI/UX Improvements
- Message reactions and feedback
- File upload for reference images
- Post preview modal
- Keyboard shortcuts
- Voice input support

## File Structure
```
src/
├── components/
│   ├── SocialMediaManager.tsx
│   ├── SocialMediaManager.css
│   ├── SocialMediaChat.tsx
│   └── SocialMediaChat.css
├── app/
│   └── dashboard/
│       ├── page.tsx
│       └── dashboard.css
└── SOCIAL_MEDIA_MANAGER.md
```

## Dependencies
- React (existing)
- Next.js (existing)
- TypeScript (existing)
- CSS3 for styling and animations

## Browser Support
- Modern browsers with CSS Grid and Flexbox support
- Mobile browsers (iOS Safari, Chrome Mobile)
- Desktop browsers (Chrome, Firefox, Safari, Edge)

---

This implementation provides a solid foundation for the social media manager feature, with room for backend integration and advanced functionality as the project evolves.
