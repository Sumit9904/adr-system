import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AuthProvider, useAuth } from './context/AuthContext';

import Login from './pages/Login';
import Register from './pages/Register';
import UserDashboard from './pages/user/Dashboard';
import UserReports from './pages/user/Reports';
import CreateReport from './pages/user/CreateReport';
import ViewReport from './pages/user/ViewReport';
import AdminDashboard from './pages/admin/Dashboard';
import AdminReports from './pages/admin/Reports';
import AdminUsers from './pages/admin/Users';
import AdminSignals from './pages/admin/Signals';
import Profile from './pages/Profile';
import NotFound from './pages/NotFound';

const PrivateRoute = ({ children, adminOnly = false }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading"><div className="spinner"></div></div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }

  return children;
};

function AppRoutes() {
  const { isAdmin } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      }
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      }

      <Route path="/dashboard" element={
        <PrivateRoute>
          {isAdmin ? <AdminDashboard /> : <UserDashboard />}
        </PrivateRoute>
      } />

      <Route path="/reports" element={<PrivateRoute><UserReports /></PrivateRoute>} />
      }
      <Route path="/reports/create" element={<PrivateRoute><CreateReport /></PrivateRoute>} />
      }
      <Route path="/reports/:id" element={<PrivateRoute><ViewReport /></PrivateRoute>} />
      }

      <Route path="/admin/reports" element={<PrivateRoute adminOnly><AdminReports /></PrivateRoute>} />
      }
      <Route path="/admin/users" element={<PrivateRoute adminOnly><AdminUsers /></PrivateRoute>} />
      }
      <Route path="/admin/signals" element={<PrivateRoute adminOnly><AdminSignals /></PrivateRoute>} />
      }

      <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
      }

      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </AuthProvider>
    </Router>
  );
}

export default App;
