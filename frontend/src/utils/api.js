import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
  changePassword: (passwords) => api.put('/auth/change-password', passwords),
};

export const reportsAPI = {
  getAll: (params) => api.get('/reports', { params }),
  getById: (id) => api.get(`/reports/${id}`),
  create: (data) => api.post('/reports', data),
  update: (id, data) => api.put(`/reports/${id}`, data),
  delete: (id) => api.delete(`/reports/${id}`),
  review: (id, data) => api.put(`/reports/${id}/review`, data),
  getSimilar: (id) => api.get(`/reports/${id}/similar`),
};

export const adminAPI = {
  getStats: () => api.get('/admin/dashboard/stats'),
  getTopDrugs: () => api.get('/admin/reports/top-drugs'),
  getUsers: () => api.get('/admin/users'),
  createUser: (data) => api.post('/admin/users', data),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  resetPassword: (id) => api.post(`/admin/users/${id}/reset-password`),
  getAuditLogs: (params) => api.get('/admin/audit-logs', { params }),
  runSignalDetection: () => api.post('/admin/signal-detection/run'),
  getSignals: () => api.get('/admin/signals'),
};

export const drugsAPI = {
  getAll: (params) => api.get('/drugs', { params }),
  create: (data) => api.post('/drugs', data),
  update: (id, data) => api.put(`/drugs/${id}`, data),
  delete: (id) => api.delete(`/drugs/${id}`),
};

export const notificationsAPI = {
  getAll: (params) => api.get('/notifications', { params }),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  markAllAsRead: () => api.put('/notifications/read-all'),
  getUnreadCount: () => api.get('/notifications/unread-count'),
};

export const exportAPI = {
  exportCSV: (params) => api.get('/export/reports/csv', { params, responseType: 'blob' }),
  exportExcel: (params) => api.get('/export/reports/excel', { params, responseType: 'blob' }),
};

export default api;
