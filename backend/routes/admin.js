const express = require('express');
const bcrypt = require('bcrypt');
const { body, validationResult } = require('express-validator');
const { supabase } = require('../config/database');
const { authenticateToken, authorizeRoles } = require('../middleware/auth');
const { auditLog } = require('../middleware/auditLog');
const { sendEmail, emailTemplates } = require('../utils/emailService');
const { detectSignals } = require('../utils/signalDetection');
const router = express.Router();

router.get('/dashboard/stats', authenticateToken, authorizeRoles('admin'), async (req, res) => {
  try {
    const [
      totalReports,
      totalUsers,
      severeReports,
      pendingReports,
      todayReports,
      severityDist,
      monthlyTrend
    ] = await Promise.all([
      supabase.from('adr_reports').select('id', { count: 'exact', head: true }),
      supabase.from('users').select('id', { count: 'exact', head: true }),
      supabase.from('adr_reports').select('id', { count: 'exact', head: true }).eq('severity', 'severe'),
      supabase.from('adr_reports').select('id', { count: 'exact', head: true }).in('status', ['submitted', 'under_review']),
      supabase.from('adr_reports').select('id', { count: 'exact', head: true }).gte('created_at', new Date().toISOString().split('T')[0]),
      supabase.from('adr_reports').select('severity').eq('status', 'approved'),
      supabase.rpc('get_monthly_trends').then(r => r.data).catch(() => [])
    ]);

    const severityDistribution = {
      mild: 0,
      moderate: 0,
      severe: 0
    };

    if (severityDist.data) {
      severityDist.data.forEach(report => {
        severityDistribution[report.severity] = (severityDistribution[report.severity] || 0) + 1;
      });
    }

    res.json({
      success: true,
      data: {
        totalReports: totalReports.count || 0,
        totalUsers: totalUsers.count || 0,
        severeReports: severeReports.count || 0,
        pendingReports: pendingReports.count || 0,
        todayReports: todayReports.count || 0,
        severityDistribution,
        monthlyTrend: monthlyTrend || []
      }
    });
  } catch (error) {
    console.error('Dashboard stats error:', error);
    res.status(500).json({ error: 'Failed to fetch dashboard statistics' });
  }
});

router.get('/reports/top-drugs', authenticateToken, authorizeRoles('admin'), async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('adr_reports')
      .select('drug_name')
      .eq('status', 'approved');

    if (error) throw error;

    const drugCounts = {};
    data.forEach(report => {
      const drug = report.drug_name.toLowerCase();
      drugCounts[drug] = (drugCounts[drug] || 0) + 1;
    });

    const topDrugs = Object.entries(drugCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([drug, count]) => ({ drug, count }));

    res.json({
      success: true,
      data: topDrugs
    });
  } catch (error) {
    console.error('Top drugs error:', error);
    res.status(500).json({ error: 'Failed to fetch top drugs' });
  }
});

router.get('/users', authenticateToken, authorizeRoles('admin'), async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('users')
      .select('id, email, full_name, role, organization, phone, is_active, created_at')
      .order('created_at', { ascending: false });

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch users' });
    }

    res.json({
      success: true,
      data
    });
  } catch (error) {
    console.error('Fetch users error:', error);
    res.status(500).json({ error: 'Server error fetching users' });
  }
});

router.post('/users', authenticateToken, authorizeRoles('admin'), [
  body('email').isEmail().normalizeEmail(),
  body('full_name').trim().notEmpty(),
  body('role').isIn(['admin', 'user']),
  body('organization').optional().trim()
], auditLog('CREATE_USER', 'user'), async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, full_name, role, organization, phone } = req.body;

    const { data: existingUser } = await supabase
      .from('users')
      .select('id')
      .eq('email', email)
      .maybeSingle();

    if (existingUser) {
      return res.status(400).json({ error: 'Email already exists' });
    }

    const tempPassword = Math.random().toString(36).slice(-10) + Math.random().toString(36).slice(-10);
    const passwordHash = await bcrypt.hash(tempPassword, 10);

    const { data: newUser, error } = await supabase
      .from('users')
      .insert({
        email,
        password_hash: passwordHash,
        full_name,
        role,
        organization,
        phone,
        is_active: true
      })
      .select('id, email, full_name, role, organization, phone, is_active, created_at')
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to create user' });
    }

    const emailData = emailTemplates.newUserCreated(email, tempPassword, full_name);
    await sendEmail({ to: email, ...emailData });

    res.status(201).json({
      success: true,
      data: newUser,
      tempPassword
    });
  } catch (error) {
    console.error('Create user error:', error);
    res.status(500).json({ error: 'Server error creating user' });
  }
});

router.put('/users/:id', authenticateToken, authorizeRoles('admin'), [
  body('full_name').optional().trim().notEmpty(),
  body('role').optional().isIn(['admin', 'user']),
  body('is_active').optional().isBoolean()
], auditLog('UPDATE_USER', 'user'), async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { full_name, role, organization, phone, is_active } = req.body;

    const { data: user, error } = await supabase
      .from('users')
      .update({ full_name, role, organization, phone, is_active })
      .eq('id', req.params.id)
      .select('id, email, full_name, role, organization, phone, is_active, created_at')
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to update user' });
    }

    res.json({
      success: true,
      data: user
    });
  } catch (error) {
    console.error('Update user error:', error);
    res.status(500).json({ error: 'Server error updating user' });
  }
});

router.post('/users/:id/reset-password', authenticateToken, authorizeRoles('admin'), auditLog('RESET_PASSWORD', 'user'), async (req, res) => {
  try {
    const { data: user } = await supabase
      .from('users')
      .select('email, full_name')
      .eq('id', req.params.id)
      .maybeSingle();

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    const tempPassword = Math.random().toString(36).slice(-10) + Math.random().toString(36).slice(-10);
    const passwordHash = await bcrypt.hash(tempPassword, 10);

    const { error } = await supabase
      .from('users')
      .update({ password_hash: passwordHash })
      .eq('id', req.params.id);

    if (error) {
      return res.status(500).json({ error: 'Failed to reset password' });
    }

    const emailData = emailTemplates.newUserCreated(user.email, tempPassword, user.full_name);
    await sendEmail({ to: user.email, ...emailData });

    res.json({
      success: true,
      message: 'Password reset successfully',
      tempPassword
    });
  } catch (error) {
    console.error('Reset password error:', error);
    res.status(500).json({ error: 'Server error resetting password' });
  }
});

router.delete('/users/:id', authenticateToken, authorizeRoles('admin'), auditLog('DELETE_USER', 'user'), async (req, res) => {
  try {
    if (req.params.id === req.user.id) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }

    const { error } = await supabase
      .from('users')
      .delete()
      .eq('id', req.params.id);

    if (error) {
      return res.status(500).json({ error: 'Failed to delete user' });
    }

    res.json({
      success: true,
      message: 'User deleted successfully'
    });
  } catch (error) {
    console.error('Delete user error:', error);
    res.status(500).json({ error: 'Server error deleting user' });
  }
});

router.get('/audit-logs', authenticateToken, authorizeRoles('admin'), async (req, res) => {
  try {
    const { page = 1, limit = 50 } = req.query;
    const from = (page - 1) * limit;
    const to = from + limit - 1;

    const { data, error, count } = await supabase
      .from('audit_logs')
      .select('*, users(full_name, email)', { count: 'exact' })
      .order('created_at', { ascending: false })
      .range(from, to);

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch audit logs' });
    }

    res.json({
      success: true,
      data,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: count,
        totalPages: Math.ceil(count / limit)
      }
    });
  } catch (error) {
    console.error('Fetch audit logs error:', error);
    res.status(500).json({ error: 'Server error fetching audit logs' });
  }
});

router.post('/signal-detection/run', authenticateToken, authorizeRoles('admin'), async (req, res) => {
  try {
    const result = await detectSignals();

    res.json({
      success: result.success,
      message: result.message || 'Signal detection completed'
    });
  } catch (error) {
    console.error('Signal detection error:', error);
    res.status(500).json({ error: 'Server error running signal detection' });
  }
});

router.get('/signals', authenticateToken, authorizeRoles('admin'), async (req, res) => {
  try {
    const { data, error } = await supabase
      .from('signal_detections')
      .select('*')
      .order('occurrence_count', { ascending: false })
      .order('last_updated', { ascending: false });

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch signals' });
    }

    res.json({
      success: true,
      data
    });
  } catch (error) {
    console.error('Fetch signals error:', error);
    res.status(500).json({ error: 'Server error fetching signals' });
  }
});

module.exports = router;
