# ADR Management System - Quick Start

Get the system running in 5 minutes.

## 1️⃣ Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# EDIT .env - Add your Supabase credentials from https://app.supabase.com/project/_/settings/api
# SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

# Start server
npm run dev
```

✅ Backend running at http://localhost:5000

## 2️⃣ Frontend Setup (2 minutes)

```bash
# In new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm start
```

✅ Frontend opening at http://localhost:3000

## 3️⃣ Login (1 minute)

**Choose one:**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@adr-system.com | Admin@123 |
| User | user@adr-system.com | User@123 |

## 🎯 What to Try

### As User:
1. Click "Create Report"
2. Fill form (Drug: Aspirin, Reaction: Rash, Severity: Moderate)
3. Submit report
4. Check "My Reports" for status

### As Admin:
1. Click "Dashboard" to see statistics
2. Go to "Reports" to see submissions
3. Click "Approve" or "Reject" a report
4. Check "Signals" for detected patterns

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| README.md | Full overview |
| API_DOCUMENTATION.md | All endpoints |
| SETUP_GUIDE.md | Detailed setup |
| SECURITY_FIXES.md | Security details |
| SYSTEM_SUMMARY.md | Complete summary |

## 🆘 Troubleshooting

| Issue | Fix |
|-------|-----|
| Port 5000 in use | Change PORT in backend/.env |
| Cannot connect to DB | Check Supabase credentials |
| Login fails | Verify JWT_SECRET length (32+ chars) |
| CORS errors | Update FRONTEND_URL in backend/.env |

## 🚀 Deploy

- Backend: See DEPLOYMENT_GUIDE.md
- Frontend: See DEPLOYMENT_GUIDE.md

---

**You're all set! Enjoy your ADR Management System!** 🎉
