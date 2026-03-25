# Project Structure

Complete folder and file structure of the ADR Management System.

## Overview

```
adr-management-system/
├── backend/                 # Node.js + Express API
├── frontend/                # React.js Application
├── README.md               # Main documentation
├── API_DOCUMENTATION.md    # Complete API reference
├── DEPLOYMENT_GUIDE.md     # Production deployment guide
├── IMPLEMENTATION_GUIDE.md # Development guide
└── PROJECT_STRUCTURE.md    # This file
```

## Backend Structure

```
backend/
├── config/
│   └── database.js         # Supabase client configuration
│
├── middleware/
│   ├── auth.js            # JWT authentication middleware
│   └── auditLog.js        # Audit logging middleware
│
├── routes/
│   ├── auth.js            # Authentication endpoints
│   ├── adr-reports.js     # ADR report CRUD operations
│   ├── admin.js           # Admin-only endpoints
│   ├── drugs.js           # Drug catalog endpoints
│   ├── notifications.js   # User notifications
│   └── export.js          # Data export endpoints
│
├── utils/
│   ├── emailService.js    # Email sending utilities
│   └── signalDetection.js # Signal detection algorithms
│
├── .env.example           # Environment variables template
├── .gitignore
├── package.json
└── server.js              # Main application entry point
```

### Key Backend Files

#### server.js
- Express app initialization
- Middleware configuration
- Route mounting
- Error handling
- Server startup

#### config/database.js
- Supabase client creation
- Database connection configuration
- Connection pooling

#### middleware/auth.js
- JWT token verification
- User authentication
- Role-based authorization
- Session management

#### middleware/auditLog.js
- Automatic activity logging
- Action tracking
- IP address capture
- Audit trail generation

#### routes/auth.js
Endpoints:
- POST /login
- POST /register
- GET /me
- PUT /change-password

#### routes/adr-reports.js
Endpoints:
- GET /reports
- POST /reports
- GET /reports/:id
- PUT /reports/:id
- DELETE /reports/:id
- PUT /reports/:id/review
- GET /reports/:id/similar

#### routes/admin.js
Endpoints:
- GET /dashboard/stats
- GET /reports/top-drugs
- GET /users
- POST /users
- PUT /users/:id
- DELETE /users/:id
- POST /users/:id/reset-password
- GET /audit-logs
- POST /signal-detection/run
- GET /signals

#### routes/drugs.js
Endpoints:
- GET /drugs
- POST /drugs
- PUT /drugs/:id
- DELETE /drugs/:id

#### routes/notifications.js
Endpoints:
- GET /notifications
- PUT /notifications/:id/read
- PUT /notifications/read-all
- GET /notifications/unread-count

#### routes/export.js
Endpoints:
- GET /reports/csv
- GET /reports/excel

#### utils/emailService.js
Functions:
- sendEmail()
- emailTemplates object
  - reportSubmitted
  - reportApproved
  - reportRejected
  - clarificationNeeded
  - newUserCreated

#### utils/signalDetection.js
Functions:
- detectSignals()
- checkDuplicateReport()
- getSimilarReports()

## Frontend Structure

```
frontend/
├── public/
│   ├── index.html          # HTML template
│   └── favicon.ico
│
├── src/
│   ├── components/
│   │   ├── Layout.js       # Main layout with sidebar
│   │   ├── Layout.css
│   │   ├── Navbar.js       # Top navigation bar
│   │   ├── Sidebar.js      # Side navigation
│   │   ├── Card.js         # Reusable card component
│   │   ├── Table.js        # Reusable table component
│   │   ├── Modal.js        # Modal dialog component
│   │   ├── Chart.js        # Chart wrapper component
│   │   └── Loading.js      # Loading spinner
│   │
│   ├── context/
│   │   └── AuthContext.js  # Authentication context & hooks
│   │
│   ├── pages/
│   │   ├── Login.js        # Login page
│   │   ├── Register.js     # Registration page
│   │   ├── Profile.js      # User profile page
│   │   ├── NotFound.js     # 404 page
│   │   ├── Auth.css        # Auth pages styling
│   │   │
│   │   ├── user/
│   │   │   ├── Dashboard.js      # User dashboard
│   │   │   ├── Reports.js        # User reports list
│   │   │   ├── CreateReport.js   # Create/edit report form
│   │   │   └── ViewReport.js     # View report details
│   │   │
│   │   └── admin/
│   │       ├── Dashboard.js      # Admin dashboard
│   │       ├── Reports.js        # Admin reports management
│   │       ├── Users.js          # User management
│   │       ├── Signals.js        # Signal detection
│   │       └── AuditLogs.js      # Audit log viewer
│   │
│   ├── utils/
│   │   ├── api.js          # API client & endpoints
│   │   ├── constants.js    # App constants
│   │   └── helpers.js      # Utility functions
│   │
│   ├── App.js              # Main app component & routing
│   ├── index.js            # React entry point
│   └── index.css           # Global styles
│
├── .env.example
├── .gitignore
├── package.json
└── README.md
```

### Key Frontend Files

#### src/App.js
- React Router setup
- Route definitions
- Protected routes
- Public routes
- Auth provider wrapper

#### src/context/AuthContext.js
Context provides:
- user: Current user object
- loading: Loading state
- login(): Login function
- register(): Registration function
- logout(): Logout function
- updateUser(): Update user data
- isAuthenticated: Boolean
- isAdmin: Boolean

#### src/utils/api.js
API modules:
- authAPI
- reportsAPI
- adminAPI
- drugsAPI
- notificationsAPI
- exportAPI

#### src/components/Layout.js
Features:
- Sidebar navigation
- Top bar with user info
- Responsive design
- Role-based menu items
- Notifications badge

#### src/pages/Login.js
Features:
- Email/password form
- Remember me option
- Link to registration
- Demo credentials display
- Form validation

#### src/pages/Register.js
Features:
- Registration form
- Password strength validation
- Confirm password
- Organization field
- Phone number field

#### src/pages/user/Dashboard.js
Features:
- Statistics cards
- Recent reports table
- Status pie chart
- Quick actions
- Notifications

#### src/pages/user/CreateReport.js
Form fields:
- Patient details
- Drug information
- Reaction details
- Outcome
- Draft/Submit options

#### src/pages/admin/Dashboard.js
Features:
- System statistics
- Top drugs chart
- Severity distribution
- Monthly trends
- Quick actions

#### src/pages/admin/Reports.js
Features:
- All reports table
- Advanced filters
- Status management
- Review modal
- Causality assessment
- Export options

#### src/pages/admin/Users.js
Features:
- Users table
- Create user form
- Edit user modal
- Reset password
- Activate/deactivate
- Role management

#### src/pages/admin/Signals.js
Features:
- Detected signals list
- Run detection button
- Signal details
- Investigation status
- Notes management

## Database Structure

```
Database: PostgreSQL (via Supabase)

Tables:
├── users
│   ├── id (uuid, pk)
│   ├── email (unique)
│   ├── password_hash
│   ├── full_name
│   ├── role
│   ├── organization
│   ├── phone
│   ├── is_active
│   ├── created_at
│   └── updated_at
│
├── drugs
│   ├── id (uuid, pk)
│   ├── name
│   ├── generic_name
│   ├── manufacturer
│   ├── description
│   └── created_at
│
├── adr_reports
│   ├── id (uuid, pk)
│   ├── report_number (unique)
│   ├── user_id (fk → users)
│   ├── status
│   ├── patient_age
│   ├── patient_gender
│   ├── patient_weight
│   ├── medical_history
│   ├── drug_id (fk → drugs)
│   ├── drug_name
│   ├── dose
│   ├── route
│   ├── frequency
│   ├── batch_number
│   ├── therapy_start_date
│   ├── therapy_end_date
│   ├── reaction_type
│   ├── severity
│   ├── onset_date
│   ├── reaction_description
│   ├── outcome
│   ├── causality_assessment
│   ├── admin_notes
│   ├── reviewed_by (fk → users)
│   ├── reviewed_at
│   ├── created_at
│   ├── updated_at
│   └── submitted_at
│
├── attachments
│   ├── id (uuid, pk)
│   ├── adr_report_id (fk → adr_reports)
│   ├── file_name
│   ├── file_path
│   ├── file_type
│   ├── file_size
│   └── uploaded_at
│
├── audit_logs
│   ├── id (uuid, pk)
│   ├── user_id (fk → users)
│   ├── action
│   ├── entity_type
│   ├── entity_id
│   ├── details (jsonb)
│   ├── ip_address
│   └── created_at
│
├── notifications
│   ├── id (uuid, pk)
│   ├── user_id (fk → users)
│   ├── adr_report_id (fk → adr_reports)
│   ├── type
│   ├── title
│   ├── message
│   ├── is_read
│   └── created_at
│
└── signal_detections
    ├── id (uuid, pk)
    ├── drug_id (fk → drugs)
    ├── drug_name
    ├── reaction_type
    ├── occurrence_count
    ├── severity_level
    ├── first_detected
    ├── last_updated
    ├── status
    └── notes

Functions:
├── generate_report_number()
├── set_report_number()
├── update_updated_at_column()
└── detect_adr_signals()

Triggers:
├── trigger_set_report_number
├── update_users_updated_at
└── update_adr_reports_updated_at

Indexes:
├── idx_adr_reports_user_id
├── idx_adr_reports_status
├── idx_adr_reports_drug_id
├── idx_adr_reports_severity
├── idx_adr_reports_created_at
├── idx_attachments_adr_report_id
├── idx_notifications_user_id
├── idx_audit_logs_user_id
└── idx_audit_logs_created_at
```

## File Sizes & Complexity

### Backend Files

| File | Lines | Complexity |
|------|-------|------------|
| server.js | ~100 | Low |
| routes/auth.js | ~150 | Medium |
| routes/adr-reports.js | ~350 | High |
| routes/admin.js | ~300 | High |
| routes/drugs.js | ~100 | Low |
| routes/notifications.js | ~80 | Low |
| routes/export.js | ~100 | Medium |
| middleware/auth.js | ~50 | Low |
| middleware/auditLog.js | ~30 | Low |
| utils/emailService.js | ~150 | Medium |
| utils/signalDetection.js | ~80 | Medium |

Total Backend: ~1,500 lines

### Frontend Files

| File | Lines | Complexity |
|------|-------|------------|
| App.js | ~80 | Medium |
| context/AuthContext.js | ~100 | Medium |
| utils/api.js | ~150 | Medium |
| components/Layout.js | ~100 | Medium |
| pages/Login.js | ~100 | Low |
| pages/Register.js | ~150 | Medium |
| pages/user/Dashboard.js | ~200 | Medium |
| pages/user/CreateReport.js | ~400 | High |
| pages/admin/Dashboard.js | ~250 | Medium |
| pages/admin/Reports.js | ~500 | High |
| pages/admin/Users.js | ~400 | High |

Total Frontend: ~2,500 lines

## Technology Breakdown

### Backend Dependencies
- express: ^4.18.2 (Web framework)
- @supabase/supabase-js: ^2.39.3 (Database client)
- bcrypt: ^5.1.1 (Password hashing)
- jsonwebtoken: ^9.0.2 (JWT authentication)
- express-validator: ^7.0.1 (Input validation)
- nodemailer: ^6.9.8 (Email sending)
- cors: ^2.8.5 (CORS handling)
- dotenv: ^16.3.1 (Environment variables)
- multer: ^1.4.5 (File uploads)

### Frontend Dependencies
- react: ^18.2.0
- react-router-dom: ^6.21.0 (Routing)
- axios: ^1.6.2 (HTTP client)
- chart.js: ^4.4.1 (Charts)
- react-chartjs-2: ^5.2.0 (React Chart.js wrapper)
- react-toastify: ^9.1.3 (Notifications)

## Development Tools

### Recommended VS Code Extensions
- ESLint
- Prettier
- GitLens
- Thunder Client (API testing)
- Docker
- PostgreSQL

### Useful Commands

```bash
# Backend
npm run dev          # Start development server
npm start            # Start production server
npm test             # Run tests

# Frontend
npm start            # Start development server
npm run build        # Build for production
npm test             # Run tests
npm run eject        # Eject from Create React App

# Database
supabase db dump     # Export schema
supabase db push     # Push migrations
supabase db reset    # Reset database
```

## Environment Files

### Backend .env
```env
PORT=5000
NODE_ENV=development
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
JWT_SECRET=
JWT_EXPIRE=7d
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=
FRONTEND_URL=http://localhost:3000
```

### Frontend .env
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_APP_NAME=ADR Management System
```

## Git Structure

```
.gitignore should include:
- node_modules/
- .env
- .env.local
- build/
- dist/
- coverage/
- *.log
- .DS_Store
```

## Testing Structure

```
backend/tests/
├── unit/
│   ├── auth.test.js
│   ├── reports.test.js
│   └── admin.test.js
├── integration/
│   ├── api.test.js
│   └── database.test.js
└── fixtures/
    └── testData.js

frontend/src/tests/
├── components/
│   ├── Layout.test.js
│   └── Modal.test.js
├── pages/
│   ├── Login.test.js
│   └── Dashboard.test.js
└── utils/
    └── api.test.js
```

## Documentation Files

- README.md - Main project documentation
- API_DOCUMENTATION.md - Complete API reference
- DEPLOYMENT_GUIDE.md - Production deployment guide
- IMPLEMENTATION_GUIDE.md - Development setup guide
- PROJECT_STRUCTURE.md - This file

## Total Project Stats

- Total Files: ~50
- Total Lines of Code: ~4,500
- Backend: ~1,500 lines
- Frontend: ~2,500 lines
- Documentation: ~500 lines
- Configuration: ~500 lines

## Maintenance

This structure supports:
- Easy navigation
- Clear separation of concerns
- Scalable architecture
- Simple testing
- Quick onboarding
- Efficient deployment
