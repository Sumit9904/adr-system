# Complete Setup Guide

Step-by-step guide to set up and run the ADR Management System.

## Prerequisites

- Node.js 16+ and npm
- Supabase account (free tier at supabase.com)
- Git
- Code editor (VS Code recommended)

## Part 1: Database Setup (Already Complete ✅)

The database schema has been fully created with:
- ✅ All 7 tables with relationships
- ✅ Row Level Security (RLS) policies (optimized)
- ✅ Indexes for performance
- ✅ Auto-generated report numbers
- ✅ Automated triggers and functions
- ✅ Sample data (drugs, admin user)

**No database migration needed - it's ready to use!**

## Part 2: Backend Setup

### Step 1: Navigate to Backend Directory

```bash
cd backend
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
# Server Configuration
PORT=5000
NODE_ENV=development

# Get these from: https://app.supabase.com/project/_/settings/api
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Generate a secure random string (min 32 characters)
JWT_SECRET=your_super_secret_jwt_key_min_32_characters
JWT_EXPIRE=7d

# Email Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
SMTP_FROM=ADR System <noreply@adr-system.com>

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Step 4: Start Backend Server

```bash
npm run dev
```

Expected output:
```
ADR Management System API Server
Server running on: http://localhost:5000
```

## Part 3: Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_APP_NAME=ADR Management System
```

### Step 4: Start Frontend Development Server

```bash
npm start
```

The app will open at `http://localhost:3000`

## Part 4: Login & Test

### Default Credentials

**Admin:**
- Email: admin@adr-system.com
- Password: Admin@123

**User:**
- Email: user@adr-system.com
- Password: User@123

## Part 5: System Features

### User Features
- ✅ Create/edit/delete draft ADR reports
- ✅ Submit reports for review
- ✅ Track report status
- ✅ View personal dashboard
- ✅ Receive notifications

### Admin Features
- ✅ Dashboard with statistics
- ✅ Review and approve reports
- ✅ Assign causality assessments
- ✅ User management
- ✅ Signal detection
- ✅ Export data
- ✅ Audit logs

## Part 6: Production Deployment

### Build Backend
```bash
cd backend
npm install --production
```

### Build Frontend
```bash
cd frontend
npm run build
```

See `DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

---

All systems ready! The application is fully functional with secure database, complete API, and professional frontend interface.
