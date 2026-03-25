# API Documentation

Complete REST API reference for the ADR Management System.

## Base URL

```
Development: http://localhost:5000/api
Production: https://your-domain.com/api
```

## Authentication

All endpoints except `/auth/login` and `/auth/register` require authentication.

**Header Format:**
```
Authorization: Bearer <your_jwt_token>
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "pagination": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "errors": [ ... ]
}
```

## Endpoints

### Authentication

#### POST /auth/login
Login to the system

**Request Body:**
```json
{
  "email": "admin@adr-system.com",
  "password": "Admin@123"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "email": "admin@adr-system.com",
    "full_name": "System Administrator",
    "role": "admin",
    "organization": "ADR Central",
    "is_active": true
  }
}
```

#### POST /auth/register
Register a new user account

**Request Body:**
```json
{
  "email": "doctor@hospital.com",
  "password": "SecurePass123",
  "full_name": "Dr. John Doe",
  "organization": "City Hospital",
  "phone": "+1234567890"
}
```

#### GET /auth/me
Get current user profile

**Response:**
```json
{
  "success": true,
  "user": { ... }
}
```

#### PUT /auth/change-password
Change user password

**Request Body:**
```json
{
  "currentPassword": "OldPass123",
  "newPassword": "NewPass456"
}
```

### ADR Reports

#### GET /reports
Get all reports (filtered by user role)

**Query Parameters:**
- `status`: draft, submitted, under_review, approved, rejected, clarification_needed
- `severity`: mild, moderate, severe
- `search`: Search in drug name, reaction type, description
- `drug_name`: Filter by drug name
- `date_from`: YYYY-MM-DD
- `date_to`: YYYY-MM-DD
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 10, max: 100)

**Example:**
```
GET /reports?status=submitted&severity=severe&page=1&limit=20
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "report_number": "ADR2024-000001",
      "user_id": "uuid",
      "status": "submitted",
      "drug_name": "Aspirin",
      "dose": "500mg",
      "route": "oral",
      "reaction_type": "Allergic reaction",
      "severity": "moderate",
      "created_at": "2024-01-15T10:30:00Z",
      "users": {
        "full_name": "Dr. John Doe",
        "email": "doctor@hospital.com",
        "organization": "City Hospital"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

#### POST /reports
Create a new ADR report

**Request Body:**
```json
{
  "status": "draft",
  "patient_age": 45,
  "patient_gender": "male",
  "patient_weight": 75.5,
  "medical_history": "Hypertension, type 2 diabetes",
  "drug_name": "Metformin",
  "dose": "1000mg",
  "route": "oral",
  "frequency": "twice daily",
  "batch_number": "MET20240115",
  "therapy_start_date": "2024-01-10",
  "therapy_end_date": "2024-01-20",
  "reaction_type": "Gastrointestinal disturbance",
  "severity": "moderate",
  "onset_date": "2024-01-12",
  "reaction_description": "Patient experienced nausea and abdominal discomfort",
  "outcome": "recovering"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "report_number": "ADR2024-000042",
    ...
  }
}
```

#### GET /reports/:id
Get specific report details

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "report_number": "ADR2024-000001",
    ...full report details...,
    "attachments": [
      {
        "id": "uuid",
        "file_name": "lab_result.pdf",
        "file_size": 524288,
        "uploaded_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

#### PUT /reports/:id
Update an ADR report (draft only for users)

**Request Body:** (Same as create, but partial updates allowed)

#### DELETE /reports/:id
Delete an ADR report (draft only for users)

#### PUT /reports/:id/review
Review and update report status (Admin only)

**Request Body:**
```json
{
  "status": "approved",
  "causality_assessment": "probable",
  "admin_notes": "Assessed as probable ADR. Drug discontinued and patient recovering."
}
```

**Causality Assessment Values:**
- `certain`
- `probable`
- `possible`
- `unlikely`
- `conditional`
- `unassessable`

#### GET /reports/:id/similar
Get similar reports for duplicate detection

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "report_number": "ADR2024-000038",
      "drug_name": "Metformin",
      "reaction_type": "Gastrointestinal disturbance",
      "severity": "moderate",
      "created_at": "2024-01-10T08:00:00Z"
    }
  ]
}
```

### Admin Endpoints

#### GET /admin/dashboard/stats
Get dashboard statistics

**Response:**
```json
{
  "success": true,
  "data": {
    "totalReports": 450,
    "totalUsers": 87,
    "severeReports": 23,
    "pendingReports": 12,
    "todayReports": 5,
    "severityDistribution": {
      "mild": 200,
      "moderate": 227,
      "severe": 23
    },
    "monthlyTrend": [
      { "month": "Jan", "count": 45 },
      { "month": "Feb", "count": 52 }
    ]
  }
}
```

#### GET /admin/reports/top-drugs
Get top 10 drugs with most reports

**Response:**
```json
{
  "success": true,
  "data": [
    { "drug": "Aspirin", "count": 45 },
    { "drug": "Metformin", "count": 38 },
    { "drug": "Lisinopril", "count": 32 }
  ]
}
```

#### GET /admin/users
Get all users

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "email": "doctor@hospital.com",
      "full_name": "Dr. John Doe",
      "role": "user",
      "organization": "City Hospital",
      "phone": "+1234567890",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /admin/users
Create a new user

**Request Body:**
```json
{
  "email": "newdoctor@hospital.com",
  "full_name": "Dr. Jane Smith",
  "role": "user",
  "organization": "General Hospital",
  "phone": "+1234567891"
}
```

**Response:**
```json
{
  "success": true,
  "data": { ...user object... },
  "tempPassword": "randomly_generated_password"
}
```

#### PUT /admin/users/:id
Update user details

**Request Body:**
```json
{
  "full_name": "Dr. Jane Smith-Johnson",
  "role": "admin",
  "organization": "Regional Hospital",
  "phone": "+1234567892",
  "is_active": false
}
```

#### POST /admin/users/:id/reset-password
Reset user password

**Response:**
```json
{
  "success": true,
  "message": "Password reset successfully",
  "tempPassword": "new_random_password"
}
```

#### DELETE /admin/users/:id
Delete a user

#### GET /admin/audit-logs
Get audit logs with pagination

**Query Parameters:**
- `page`: Page number
- `limit`: Items per page (default: 50)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "action": "REVIEW_ADR_REPORT",
      "entity_type": "adr_report",
      "entity_id": "uuid",
      "details": { ... },
      "ip_address": "192.168.1.1",
      "created_at": "2024-01-15T10:30:00Z",
      "users": {
        "full_name": "Admin User",
        "email": "admin@adr-system.com"
      }
    }
  ],
  "pagination": { ... }
}
```

#### POST /admin/signal-detection/run
Run signal detection algorithm

**Response:**
```json
{
  "success": true,
  "message": "Signal detection completed"
}
```

#### GET /admin/signals
Get all detected signals

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "drug_name": "Aspirin",
      "reaction_type": "Allergic reaction",
      "occurrence_count": 15,
      "severity_level": "moderate",
      "first_detected": "2024-01-01T00:00:00Z",
      "last_updated": "2024-01-15T10:30:00Z",
      "status": "active",
      "notes": null
    }
  ]
}
```

### Drugs

#### GET /drugs
Get all drugs

**Query Parameters:**
- `search`: Search by name, generic name, or manufacturer
- `page`: Page number
- `limit`: Items per page (default: 50)

#### POST /drugs (Admin only)
Add a new drug

**Request Body:**
```json
{
  "name": "Aspirin",
  "generic_name": "Acetylsalicylic Acid",
  "manufacturer": "Bayer",
  "description": "Pain reliever and anti-inflammatory"
}
```

#### PUT /drugs/:id (Admin only)
Update drug information

#### DELETE /drugs/:id (Admin only)
Delete a drug

### Notifications

#### GET /notifications
Get user notifications

**Query Parameters:**
- `is_read`: true/false
- `page`: Page number
- `limit`: Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "adr_report_id": "uuid",
      "type": "report_approved",
      "title": "Report Approved",
      "message": "Your ADR report ADR2024-000042 has been approved",
      "is_read": false,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": { ... }
}
```

#### PUT /notifications/:id/read
Mark notification as read

#### PUT /notifications/read-all
Mark all notifications as read

#### GET /notifications/unread-count
Get unread notification count

**Response:**
```json
{
  "success": true,
  "count": 5
}
```

### Export

#### GET /export/reports/csv
Export reports as CSV

**Query Parameters:** (Same as GET /reports)

**Response:** CSV file download

#### GET /export/reports/excel
Export reports as Excel

**Query Parameters:** (Same as GET /reports)

**Response:** Excel file download

## Error Codes

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing or invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `409` - Conflict (duplicate detection)
- `500` - Internal Server Error

## Rate Limiting

- No rate limiting in development
- Production: 100 requests per 15 minutes per IP

## Pagination

All list endpoints support pagination with consistent format:

```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

## Best Practices

1. Always check the `success` field in responses
2. Handle errors gracefully with appropriate user feedback
3. Store JWT token securely (not in localStorage for production)
4. Implement request debouncing for search
5. Use proper HTTP methods (GET, POST, PUT, DELETE)
6. Include pagination for large datasets
7. Validate input on both client and server

## Postman Collection

Import this into Postman for testing:

```json
{
  "info": { "name": "ADR Management System API" },
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/auth/login",
            "body": {
              "mode": "raw",
              "raw": "{\"email\":\"admin@adr-system.com\",\"password\":\"Admin@123\"}"
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:5000/api"
    }
  ]
}
```

## WebSocket (Future)

Real-time notifications will be available via WebSocket:

```javascript
const socket = io('http://localhost:5000');
socket.on('notification', (data) => {
  console.log('New notification:', data);
});
```
