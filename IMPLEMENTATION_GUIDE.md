# Complete Implementation Guide

This guide provides all the remaining code needed to complete the ADR Management System.

## Frontend Pages to Create

### 1. Register Page (`frontend/src/pages/Register.js`)

```javascript
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { toast } from 'react-toastify';
import './Auth.css';

const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    organization: '',
    phone: '',
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...registerData } = formData;
      await register(registerData);
      toast.success('Registration successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>ADR Management System</h1>
          <p>Create Your Account</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h2>Register</h2>

          <div className="form-group">
            <label className="form-label">Full Name *</label>
            <input type="text" name="full_name" className="form-control"
              value={formData.full_name} onChange={handleChange} required
              placeholder="Dr. John Doe" />
          </div>

          <div className="form-group">
            <label className="form-label">Email Address *</label>
            <input type="email" name="email" className="form-control"
              value={formData.email} onChange={handleChange} required
              placeholder="your.email@hospital.com" />
          </div>

          <div className="form-group">
            <label className="form-label">Organization</label>
            <input type="text" name="organization" className="form-control"
              value={formData.organization} onChange={handleChange}
              placeholder="Your Hospital/Organization" />
          </div>

          <div className="form-group">
            <label className="form-label">Phone Number</label>
            <input type="tel" name="phone" className="form-control"
              value={formData.phone} onChange={handleChange}
              placeholder="+1234567890" />
          </div>

          <div className="form-group">
            <label className="form-label">Password *</label>
            <input type="password" name="password" className="form-control"
              value={formData.password} onChange={handleChange} required
              placeholder="Min. 8 characters" />
          </div>

          <div className="form-group">
            <label className="form-label">Confirm Password *</label>
            <input type="password" name="confirmPassword" className="form-control"
              value={formData.confirmPassword} onChange={handleChange} required
              placeholder="Re-enter password" />
          </div>

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>

          <div className="auth-footer">
            <p>Already have an account? <Link to="/login">Login here</Link></p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
```

### 2. User Dashboard (`frontend/src/pages/user/Dashboard.js`)

```javascript
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import Layout from '../../components/Layout';
import { reportsAPI } from '../../utils/api';
import { Pie, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const UserDashboard = () => {
  const [stats, setStats] = useState({
    total: 0,
    draft: 0,
    submitted: 0,
    approved: 0,
    rejected: 0,
  });
  const [recentReports, setRecentReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await reportsAPI.getAll({ limit: 5 });
      const reports = response.data.data;

      setRecentReports(reports);

      const statsData = reports.reduce((acc, report) => {
        acc.total++;
        acc[report.status] = (acc[report.status] || 0) + 1;
        return acc;
      }, { total: 0, draft: 0, submitted: 0, approved: 0, rejected: 0 });

      setStats(statsData);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    draft: '#95a5a6',
    submitted: '#3498db',
    under_review: '#f39c12',
    approved: '#27ae60',
    rejected: '#e74c3c',
    clarification_needed: '#e67e22',
  };

  const statusData = {
    labels: ['Draft', 'Submitted', 'Approved', 'Rejected'],
    datasets: [{
      data: [stats.draft, stats.submitted, stats.approved, stats.rejected],
      backgroundColor: ['#95a5a6', '#3498db', '#27ae60', '#e74c3c'],
    }],
  };

  if (loading) {
    return <Layout><div className="loading"><div className="spinner"></div></div></Layout>;
  }

  return (
    <Layout>
      <div className="container">
        <h1>My Dashboard</h1>

        <div className="grid grid-4 mt-2">
          <div className="card">
            <h3>Total Reports</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#3498db' }}>
              {stats.total}
            </div>
          </div>
          <div className="card">
            <h3>Draft</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#95a5a6' }}>
              {stats.draft}
            </div>
          </div>
          <div className="card">
            <h3>Submitted</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#f39c12' }}>
              {stats.submitted}
            </div>
          </div>
          <div className="card">
            <h3>Approved</h3>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#27ae60' }}>
              {stats.approved}
            </div>
          </div>
        </div>

        <div className="grid grid-2 mt-2">
          <div className="card">
            <h3>Report Status Distribution</h3>
            <div style={{ maxWidth: '400px', margin: '0 auto' }}>
              <Pie data={statusData} />
            </div>
          </div>

          <div className="card">
            <h3>Quick Actions</h3>
            <div className="flex" style={{ flexDirection: 'column', gap: '10px' }}>
              <Link to="/reports/create" className="btn btn-primary">
                Create New ADR Report
              </Link>
              <Link to="/reports" className="btn btn-secondary">
                View All My Reports
              </Link>
            </div>
          </div>
        </div>

        <div className="card mt-2">
          <h3>Recent Reports</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Report Number</th>
                <th>Drug</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {recentReports.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center">No reports yet. Create your first report!</td>
                </tr>
              ) : (
                recentReports.map(report => (
                  <tr key={report.id}>
                    <td>{report.report_number}</td>
                    <td>{report.drug_name}</td>
                    <td>
                      <span className={`badge badge-${report.severity === 'severe' ? 'danger' : report.severity === 'moderate' ? 'warning' : 'success'}`}>
                        {report.severity}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-info">{report.status}</span>
                    </td>
                    <td>{new Date(report.created_at).toLocaleDateString()}</td>
                    <td>
                      <Link to={`/reports/${report.id}`} className="btn btn-sm btn-primary">
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
};

export default UserDashboard;
```

### 3. Admin Dashboard (`frontend/src/pages/admin/Dashboard.js`)

```javascript
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import Layout from '../../components/Layout';
import { adminAPI } from '../../utils/api';
import { Pie, Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, PointElement, LineElement);

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalReports: 0,
    totalUsers: 0,
    severeReports: 0,
    pendingReports: 0,
    todayReports: 0,
  });
  const [topDrugs, setTopDrugs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, drugsRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getTopDrugs(),
      ]);

      setStats(statsRes.data.data);
      setTopDrugs(drugsRes.data.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const topDrugsData = {
    labels: topDrugs.map(d => d.drug),
    datasets: [{
      label: 'Number of Reports',
      data: topDrugs.map(d => d.count),
      backgroundColor: '#3498db',
    }],
  };

  if (loading) {
    return <Layout><div className="loading"><div className="spinner"></div></div></Layout>;
  }

  return (
    <Layout>
      <div className="container">
        <div className="flex-between mb-2">
          <h1>Admin Dashboard</h1>
          <Link to="/admin/reports" className="btn btn-primary">
            Manage Reports
          </Link>
        </div>

        <div className="grid grid-4">
          <div className="card">
            <small style={{ color: '#7f8c8d' }}>Total Reports</small>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#3498db' }}>
              {stats.totalReports}
            </div>
          </div>
          <div className="card">
            <small style={{ color: '#7f8c8d' }}>Total Users</small>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#2ecc71' }}>
              {stats.totalUsers}
            </div>
          </div>
          <div className="card">
            <small style={{ color: '#7f8c8d' }}>Severe Cases</small>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#e74c3c' }}>
              {stats.severeReports}
            </div>
          </div>
          <div className="card">
            <small style={{ color: '#7f8c8d' }}>Pending Review</small>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#f39c12' }}>
              {stats.pendingReports}
            </div>
          </div>
        </div>

        <div className="grid grid-2 mt-2">
          <div className="card">
            <h3>Top 10 Drugs with ADRs</h3>
            <Bar data={topDrugsData} options={{
              responsive: true,
              plugins: { legend: { display: false } }
            }} />
          </div>

          <div className="card">
            <h3>Quick Actions</h3>
            <div className="flex" style={{ flexDirection: 'column', gap: '10px', marginTop: '20px' }}>
              <Link to="/admin/reports" className="btn btn-primary">
                Review Pending Reports ({stats.pendingReports})
              </Link>
              <Link to="/admin/users" className="btn btn-success">
                Manage Users
              </Link>
              <Link to="/admin/signals" className="btn btn-warning">
                Signal Detection
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default AdminDashboard;
```

### 4. Other Essential Pages

Create these additional pages with similar structure:

**frontend/src/pages/NotFound.js**
**frontend/src/pages/Profile.js**
**frontend/src/pages/user/Reports.js**
**frontend/src/pages/user/CreateReport.js**
**frontend/src/pages/user/ViewReport.js**
**frontend/src/pages/admin/Reports.js**
**frontend/src/pages/admin/Users.js**
**frontend/src/pages/admin/Signals.js**

Each page should:
1. Import Layout component
2. Use appropriate API calls from utils/api.js
3. Implement loading states
4. Handle errors with toast notifications
5. Follow the same styling patterns

## Quick Start Commands

### Terminal 1 - Backend
```bash
cd backend
npm install
cp .env.example .env
# Edit .env with your Supabase credentials
npm run dev
```

### Terminal 2 - Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm start
```

### Terminal 3 - Access Application
```
Open: http://localhost:3000
Login: admin@adr-system.com / Admin@123
```

## Testing Workflow

1. **Login as Admin**
   - Email: admin@adr-system.com
   - Password: Admin@123

2. **Create a User**
   - Go to Admin → Users
   - Click "Create User"
   - Note the temporary password

3. **Login as User**
   - Use new user credentials
   - Create an ADR report
   - Save as draft
   - Submit report

4. **Login as Admin Again**
   - Review submitted report
   - Approve/Reject
   - Check notifications

5. **Verify Email**
   - Check configured email
   - Verify notification emails

## Next Steps

1. Complete all frontend pages using the patterns shown
2. Add file upload functionality using multer
3. Implement real-time notifications with WebSocket
4. Add comprehensive unit tests
5. Deploy to production

## Support

For any issues or questions:
- Check README.md for detailed documentation
- Review API endpoints in server.js
- Test API using Postman/Thunder Client
- Check browser console for frontend errors
- Check terminal for backend errors

Good luck with your implementation!
