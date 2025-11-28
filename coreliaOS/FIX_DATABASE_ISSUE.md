# 🔧 Fix Content Calendar Database Issue

## Problem Diagnosis
You're experiencing "Failed to load content calendar" because:
1. **Empty Database**: Your `db.sqlite3` is 0 bytes (corrupted/empty)
2. **Repeated OPTIONS Requests**: Cache-busting causing excessive polling
3. **Model Mismatch**: Potential data model compatibility issues

## ✅ Complete Solution

### Step 1: Reset Database (Recommended)
```bash
# Navigate to Django project
cd /Users/r/Desktop/spaceai.tmp/coreliaOS

# Run the database reset script
python reset_database.py
```

### Step 2: Manual Database Reset (Alternative)
If the script fails, do this manually:

```bash
# Remove corrupted database
rm db.sqlite3

# Remove old migrations (keep __init__.py files)
find . -path "*/migrations/*.py" -not -name "__init__.py" -exec rm {} \;

# Create fresh migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Step 3: Start Server
```bash
# Start Django development server
python manage.py runserver
```

### Step 4: Test Frontend
```bash
# In another terminal, navigate to frontend
cd /Users/r/Desktop/spaceai.tmp/lance

# Start Next.js development server
npm run dev
```

## 🔍 What We Fixed

### Frontend Improvements:
1. **Reduced Aggressive Cache Busting** - Less frequent API calls
2. **Better Error Handling** - Enhanced error state with retry options
3. **Improved Retry Logic** - Exponential backoff and proper cache clearing
4. **Enhanced Error UI** - More helpful error messages and actions

### Backend Preparation:
1. **Database Reset Script** - Automated database recreation
2. **Migration Cleanup** - Fresh migration state
3. **Proper User Setup** - Automated superuser creation

## 🚨 If Problems Persist

### Check These:
1. **Django Server Running**: Verify `python manage.py runserver` is active
2. **Port Conflicts**: Ensure no other services on port 8000
3. **Database Permissions**: Check if Django can write to the directory
4. **CORS Settings**: Verify frontend can access backend API

### Debug Commands:
```bash
# Check database tables
python manage.py dbshell
.tables

# Check migrations status
python manage.py showmigrations

# Check for errors in admin
python manage.py check
```

## 🎯 Expected Result
After following these steps:
- ✅ Database will be fresh and properly structured
- ✅ Content calendar will load without errors
- ✅ All CRUD operations will work correctly
- ✅ Cache invalidation will be optimized
- ✅ Error handling will be more user-friendly

## 📝 Notes
- The reset script preserves no existing data (fresh start)
- All content calendars and posts will need to be recreated
- User accounts will need to be recreated (except admin)
- This fixes model compatibility issues from code changes
