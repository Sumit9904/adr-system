# Advanced ADR (Adverse Drug Reaction) Management System

A comprehensive, enterprise-grade web application for managing and reporting adverse drug reactions with multi-role authentication, analytics, signal detection, and automated workflows.

## 🚀 Features

### Core Functionality
- **Multi-Role Authentication**: Admin and Healthcare Professional roles with JWT-based security
- **Advanced ADR Reporting**: Comprehensive forms with patient, drug, and reaction details
- **Draft & Submit Workflow**: Save drafts and submit when ready
- **Approval Workflow**: Admin review, approve, reject, or request clarification
- **Signal Detection**: Automated detection of repeated ADR patterns
- **Duplicate Detection**: Identifies potential duplicate submissions
- **Analytics Dashboard**: Real-time statistics and charts
- **Export Functionality**: CSV and Excel export capabilities
- **Email Notifications**: Automated notifications for all key actions
- **Audit Logging**: Complete trail of all system activities
- **File Attachments**: Upload images and reports (implementation ready)

### User Panel
- Submit and manage ADR reports
- Track report status
- View personal analytics
- Edit draft reports
- Receive notifications

### Admin Panel
- Review and approve/reject reports
- User management (create, edit, deactivate users)
- Comprehensive analytics dashboard
- Signal detection management
- Audit log viewing
- Export filtered data
- Causality assessment (WHO-UMC scale)

## 🛠️ Technology Stack

### Backend
- **Framework**: Node.js with Express.js
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Express-validator
- **Email**: Nodemailer
- **Security**: bcrypt for password hashing

### Frontend
- **Framework**: React.js 18
- **Routing**: React Router v6
- **State Management**: Context API
- **HTTP Client**: Axios
- **Charts**: Chart.js with react-chartjs-2
- **Notifications**: React-Toastify
- **Styling**: Custom CSS with modern design

### Database
- **Platform**: Supabase (PostgreSQL)
- **ORM**: Supabase JavaScript Client
- **Security**: Row Level Security (RLS) policies

## 📋 Prerequisites

- Node.js >= 14.x
- npm or yarn
- Supabase account (free tier works)
- SMTP server for emails (optional, Gmail works)

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd adr-management-system
```

### 2. Database Setup

The database schema has already been created via Supabase migrations. It includes:

**Tables:**
- `users` - User accounts with role-based access
- `drugs` - Drug catalog
- `adr_reports` - Main ADR reports
- `attachments` - File attachments for reports
- `audit_logs` - System activity logs
- `notifications` - User notifications
- `signal_detections` - Automated signal detection results

**Key Features:**
- Auto-generated report numbers (ADR2024-000001 format)
- Row Level Security (RLS) enabled on all tables
- Automated signal detection function
- Sample drugs and default admin user pre-loaded

### 3. Backend Setup

```bash
cd backend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

**Edit `.env` file:**

```env
PORT=5000
NODE_ENV=development

# Get these from your Supabase project settings
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Generate a secure random string
JWT_SECRET=your_super_secret_jwt_key_min_32_characters

# JWT token expiration
JWT_EXPIRE=7d

# SMTP Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM=ADR System <noreply@adr-system.com>

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

**Start the backend server:**

```bash
npm run dev
```

The API server will run on `http://localhost:5000`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

**Edit `.env` file:**

```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_APP_NAME=ADR Management System
```

**Start the frontend development server:**

```bash
npm start
```

The application will open at `http://localhost:3000`

## 👥 Default Users

### Admin Account
- **Email**: admin@adr-system.com
- **Password**: Admin@123
- **Role**: Administrator

### User Account
- **Email**: user@adr-system.com
- **Password**: User@123
- **Role**: Healthcare Professional

## 📱 API Documentation

### Authentication Endpoints

#### POST `/api/auth/login`
Login with email and password
```json
{
  "email": "admin@adr-system.com",
  "password": "Admin@123"
}
```

#### POST `/api/auth/register`
Register new user account
```json
{
  "email": "newuser@example.com",
  "password": "SecurePass123",
  "full_name": "Dr. John Doe",
  "organization": "City Hospital",
  "phone": "+1234567890"
}
```

#### GET `/api/auth/me`
Get current user profile (requires authentication)

#### PUT `/api/auth/change-password`
Change user password
```json
{
  "currentPassword": "OldPass123",
  "newPassword": "NewPass123"
}
```

### ADR Reports Endpoints

#### GET `/api/reports`
Get all reports (with filters)
- Query params: `status`, `severity`, `search`, `drug_name`, `date_from`, `date_to`, `page`, `limit`

#### POST `/api/reports`
Create new ADR report
```json
{
  "drug_name": "Aspirin",
  "dose": "500mg",
  "route": "oral",
  "frequency": "twice daily",
  "batch_number": "BATCH123",
  "therapy_start_date": "2024-01-01",
  "patient_age": 45,
  "patient_gender": "male",
  "patient_weight": 75,
  "reaction_type": "Allergic reaction",
  "reaction_description": "Developed rash and itching",
  "severity": "moderate",
  "onset_date": "2024-01-05",
  "outcome": "recovering",
  "status": "draft"
}
```

#### GET `/api/reports/:id`
Get specific report details

#### PUT `/api/reports/:id`
Update report (draft reports only for users)

#### DELETE `/api/reports/:id`
Delete report (draft reports only for users)

#### PUT `/api/reports/:id/review` (Admin only)
Review and update report status
```json
{
  "status": "approved",
  "causality_assessment": "probable",
  "admin_notes": "Assessment completed"
}
```

#### GET `/api/reports/:id/similar`
Get similar reports for duplicate detection

### Admin Endpoints

#### GET `/api/admin/dashboard/stats`
Get dashboard statistics

#### GET `/api/admin/reports/top-drugs`
Get top 10 drugs with most reports

#### GET `/api/admin/users`
Get all users

#### POST `/api/admin/users`
Create new user
```json
{
  "email": "newdoctor@hospital.com",
  "full_name": "Dr. Jane Smith",
  "role": "user",
  "organization": "General Hospital",
  "phone": "+1234567890"
}
```

#### PUT `/api/admin/users/:id`
Update user details

#### DELETE `/api/admin/users/:id`
Delete user

#### POST `/api/admin/users/:id/reset-password`
Reset user password

#### GET `/api/admin/audit-logs`
Get audit logs with pagination

#### POST `/api/admin/signal-detection/run`
Run signal detection algorithm

#### GET `/api/admin/signals`
Get all detected signals

### Drugs Endpoints

#### GET `/api/drugs`
Get all drugs (with search)

#### POST `/api/drugs` (Admin only)
Add new drug

#### PUT `/api/drugs/:id` (Admin only)
Update drug

#### DELETE `/api/drugs/:id` (Admin only)
Delete drug

### Notifications Endpoints

#### GET `/api/notifications`
Get user notifications

#### PUT `/api/notifications/:id/read`
Mark notification as read

#### PUT `/api/notifications/read-all`
Mark all notifications as read

#### GET `/api/notifications/unread-count`
Get unread notification count

### Export Endpoints

#### GET `/api/export/reports/csv`
Export reports as CSV

#### GET `/api/export/reports/excel`
Export reports as Excel

## 🎨 Frontend Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Layout.js              # Main layout with sidebar
│   │   ├── Layout.css
│   │   └── ...
│   ├── context/
│   │   └── AuthContext.js         # Authentication context
│   ├── pages/
│   │   ├── Login.js
│   │   ├── Register.js
│   │   ├── Profile.js
│   │   ├── NotFound.js
│   │   ├── user/
│   │   │   ├── Dashboard.js       # User dashboard
│   │   │   ├── Reports.js         # User reports list
│   │   │   ├── CreateReport.js    # Create/edit report form
│   │   │   └── ViewReport.js      # View report details
│   │   └── admin/
│   │       ├── Dashboard.js       # Admin dashboard with analytics
│   │       ├── Reports.js         # Admin reports management
│   │       ├── Users.js           # User management
│   │       └── Signals.js         # Signal detection
│   ├── utils/
│   │   └── api.js                 # API client
│   ├── App.js
│   ├── index.js
│   └── index.css
└── package.json
```

## 🔐 Security Features

1. **JWT Authentication**: Secure token-based authentication
2. **Password Hashing**: bcrypt with salt rounds
3. **Row Level Security**: Database-level access control
4. **Role-Based Access Control**: Admin and user permissions
5. **Input Validation**: Server-side validation with express-validator
6. **SQL Injection Prevention**: Parameterized queries
7. **CORS Configuration**: Controlled cross-origin access
8. **Audit Logging**: Complete activity trail

## 📊 Key Features Explained

### Signal Detection
The system automatically detects patterns in ADR reports:
- Identifies drugs with 3+ similar reactions in 90 days
- Tracks severity trends
- Flags for investigation
- Admin can manage and update signal status

### Duplicate Detection
Before submission, the system checks for:
- Same drug, reaction, and patient age
- Within 30-day window
- Same user submissions
- Warns users about potential duplicates

### Causality Assessment (WHO-UMC Scale)
- **Certain**: Clear temporal relationship, no alternative explanation
- **Probable**: Reasonable time relationship, unlikely to be attributed to other causes
- **Possible**: Reasonable time relationship but could be explained by other factors
- **Unlikely**: Temporal relationship makes it improbable
- **Conditional**: More data required for proper assessment
- **Unassessable**: Cannot be judged

### Email Notifications
Automated emails sent for:
- Report submission confirmation
- Report approval
- Report rejection
- Clarification requests
- New user account creation

## 🧪 Testing

### Backend Testing

```bash
cd backend
npm test
```

### Frontend Testing

```bash
cd frontend
npm test
```

### Manual Testing Checklist

**User Flow:**
- [ ] Register new account
- [ ] Login as user
- [ ] Create draft ADR report
- [ ] Submit ADR report
- [ ] View report status
- [ ] Edit draft report
- [ ] Delete draft report
- [ ] View notifications
- [ ] Change password
- [ ] Logout

**Admin Flow:**
- [ ] Login as admin
- [ ] View dashboard statistics
- [ ] Review submitted reports
- [ ] Approve report
- [ ] Reject report
- [ ] Request clarification
- [ ] Assign causality assessment
- [ ] Create new user
- [ ] Reset user password
- [ ] Deactivate user
- [ ] Run signal detection
- [ ] View signals
- [ ] Export data (CSV/Excel)
- [ ] View audit logs

## 🚀 Deployment

### Backend Deployment (Heroku Example)

```bash
cd backend

# Login to Heroku
heroku login

# Create app
heroku create adr-backend-api

# Set environment variables
heroku config:set NODE_ENV=production
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_SERVICE_ROLE_KEY=your_key
heroku config:set JWT_SECRET=your_secret
# ... set all other env variables

# Deploy
git push heroku main
```

### Frontend Deployment (Vercel Example)

```bash
cd frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard:
# REACT_APP_API_URL=https://your-backend-url.herokuapp.com/api
```

### Environment Variables Checklist

**Backend:**
- ✅ PORT
- ✅ NODE_ENV
- ✅ SUPABASE_URL
- ✅ SUPABASE_ANON_KEY
- ✅ SUPABASE_SERVICE_ROLE_KEY
- ✅ JWT_SECRET
- ✅ JWT_EXPIRE
- ✅ SMTP_HOST
- ✅ SMTP_PORT
- ✅ SMTP_USER
- ✅ SMTP_PASSWORD
- ✅ SMTP_FROM
- ✅ FRONTEND_URL

**Frontend:**
- ✅ REACT_APP_API_URL

## 📝 Sample Test Data

### Sample ADR Reports

```json
{
  "drug_name": "Amoxicillin",
  "dose": "500mg",
  "route": "oral",
  "frequency": "three times daily",
  "batch_number": "AMX20240115",
  "therapy_start_date": "2024-01-15",
  "therapy_end_date": "2024-01-22",
  "patient_age": 32,
  "patient_gender": "female",
  "patient_weight": 62,
  "medical_history": "No known allergies",
  "reaction_type": "Skin rash",
  "reaction_description": "Developed red, itchy rash on arms and torso after 3 days of treatment",
  "severity": "moderate",
  "onset_date": "2024-01-18",
  "outcome": "recovered",
  "status": "submitted"
}
```

## 🐛 Troubleshooting

### Common Issues

**Issue: Cannot connect to database**
- Solution: Check Supabase credentials in `.env` file
- Verify Supabase project is active

**Issue: JWT token expired**
- Solution: Login again to get new token
- Check JWT_EXPIRE setting

**Issue: Email not sending**
- Solution: Verify SMTP credentials
- For Gmail, use App Password not regular password
- Enable "Less secure app access" if using Gmail

**Issue: CORS errors**
- Solution: Check FRONTEND_URL in backend .env
- Verify CORS configuration in server.js

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Express.js Guide](https://expressjs.com/)
- [React Documentation](https://react.dev/)
- [JWT Best Practices](https://jwt.io/introduction)
- [WHO-UMC Causality Assessment](https://www.who.int/medicines/areas/quality_safety/safety_efficacy/WHOcausality_assessment.pdf)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👨‍💻 Support

For support, email support@adr-system.com or open an issue in the repository.

## 🎯 Roadmap

- [ ] Mobile application (React Native)
- [ ] Advanced analytics with ML predictions
- [ ] Multi-language support
- [ ] Real-time notifications (WebSocket)
- [ ] Integration with WHO VigiBase
- [ ] Blockchain-based audit trail
- [ ] PDF report generation
- [ ] Advanced search with Elasticsearch
- [ ] Two-factor authentication

---

**Built with ❤️ for Healthcare Safety**
