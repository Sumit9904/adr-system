require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');

const authRoutes = require('./routes/auth');
const adrReportRoutes = require('./routes/adr-reports');
const adminRoutes = require('./routes/admin');
const drugRoutes = require('./routes/drugs');
const notificationRoutes = require('./routes/notifications');
const exportRoutes = require('./routes/export');

const app = express();

app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

app.get('/api/health', (req, res) => {
  res.json({
    success: true,
    message: 'ADR Management System API is running',
    timestamp: new Date().toISOString()
  });
});

app.use('/api/auth', authRoutes);
app.use('/api/reports', adrReportRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/drugs', drugRoutes);
app.use('/api/notifications', notificationRoutes);
app.use('/api/export', exportRoutes);

app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found'
  });
});

app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(err.status || 500).json({
    success: false,
    error: err.message || 'Internal server error'
  });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`
  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║   ADR Management System API Server                       ║
  ║   Version: 1.0.0                                          ║
  ║                                                           ║
  ║   Server running on: http://localhost:${PORT}              ║
  ║   Environment: ${process.env.NODE_ENV || 'development'}                              ║
  ║                                                           ║
  ║   API Documentation: /api/health                          ║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;
