import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { notificationsAPI } from '../utils/api';
import './Layout.css';

const Layout = ({ children }) => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    fetchUnreadCount();
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.count);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>ADR System</h2>
        </div>

        <nav className="sidebar-nav">
          <Link to="/dashboard" className="nav-link">
            <span className="icon">📊</span>
            <span>Dashboard</span>
          </Link>

          {isAdmin ? (
            <>
              <Link to="/admin/reports" className="nav-link">
                <span className="icon">📋</span>
                <span>All Reports</span>
              </Link>
              <Link to="/admin/users" className="nav-link">
                <span className="icon">👥</span>
                <span>Users</span>
              </Link>
              <Link to="/admin/signals" className="nav-link">
                <span className="icon">⚠️</span>
                <span>Signal Detection</span>
              </Link>
            </>
          ) : (
            <>
              <Link to="/reports" className="nav-link">
                <span className="icon">📋</span>
                <span>My Reports</span>
              </Link>
              <Link to="/reports/create" className="nav-link">
                <span className="icon">➕</span>
                <span>New Report</span>
              </Link>
            </>
          )}

          <Link to="/profile" className="nav-link">
            <span className="icon">⚙️</span>
            <span>Profile</span>
          </Link>
        </nav>

        <div className="sidebar-footer">
          <button onClick={handleLogout} className="btn btn-danger btn-block">
            Logout
          </button>
        </div>
      </aside>

      <div className="main-content">
        <header className="topbar">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
            ☰
          </button>

          <div className="topbar-right">
            <div className="user-info">
              <span className="user-name">{user?.full_name}</span>
              <span className="user-role badge badge-info">{user?.role}</span>
            </div>
          </div>
        </header>

        <main className="content">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
