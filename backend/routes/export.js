const express = require('express');
const { supabase } = require('../config/database');
const { authenticateToken, authorizeRoles } = require('../middleware/auth');
const router = express.Router();

const generateCSV = (data) => {
  if (!data || data.length === 0) return '';

  const headers = [
    'Report Number', 'Status', 'Submitted Date', 'Reporter', 'Organization',
    'Patient Age', 'Patient Gender', 'Patient Weight',
    'Drug Name', 'Dose', 'Route', 'Frequency', 'Batch Number',
    'Reaction Type', 'Severity', 'Onset Date', 'Reaction Description',
    'Outcome', 'Causality Assessment', 'Admin Notes', 'Reviewed By', 'Reviewed At'
  ];

  const csvRows = [headers.join(',')];

  data.forEach(report => {
    const row = [
      report.report_number,
      report.status,
      report.submitted_at || '',
      report.users?.full_name || '',
      report.users?.organization || '',
      report.patient_age || '',
      report.patient_gender || '',
      report.patient_weight || '',
      report.drug_name,
      report.dose || '',
      report.route || '',
      report.frequency || '',
      report.batch_number || '',
      report.reaction_type,
      report.severity,
      report.onset_date || '',
      `"${(report.reaction_description || '').replace(/"/g, '""')}"`,
      report.outcome || '',
      report.causality_assessment || '',
      `"${(report.admin_notes || '').replace(/"/g, '""')}"`,
      report.reviewed_by || '',
      report.reviewed_at || ''
    ];
    csvRows.push(row.join(','));
  });

  return csvRows.join('\n');
};

router.get('/reports/csv', authenticateToken, async (req, res) => {
  try {
    const { status, severity, date_from, date_to } = req.query;

    let query = supabase
      .from('adr_reports')
      .select('*, users!adr_reports_user_id_fkey(full_name, email, organization)');

    if (req.user.role !== 'admin') {
      query = query.eq('user_id', req.user.id);
    }

    if (status) query = query.eq('status', status);
    if (severity) query = query.eq('severity', severity);
    if (date_from) query = query.gte('created_at', date_from);
    if (date_to) query = query.lte('created_at', date_to);

    const { data, error } = await query.order('created_at', { ascending: false });

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch reports for export' });
    }

    const csv = generateCSV(data);

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename=adr_reports_${Date.now()}.csv`);
    res.send(csv);
  } catch (error) {
    console.error('Export CSV error:', error);
    res.status(500).json({ error: 'Server error exporting data' });
  }
});

router.get('/reports/excel', authenticateToken, async (req, res) => {
  try {
    const { status, severity, date_from, date_to } = req.query;

    let query = supabase
      .from('adr_reports')
      .select('*, users!adr_reports_user_id_fkey(full_name, email, organization)');

    if (req.user.role !== 'admin') {
      query = query.eq('user_id', req.user.id);
    }

    if (status) query = query.eq('status', status);
    if (severity) query = query.eq('severity', severity);
    if (date_from) query = query.gte('created_at', date_from);
    if (date_to) query = query.lte('created_at', date_to);

    const { data, error } = await query.order('created_at', { ascending: false });

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch reports for export' });
    }

    const csv = generateCSV(data);

    res.setHeader('Content-Type', 'application/vnd.ms-excel');
    res.setHeader('Content-Disposition', `attachment; filename=adr_reports_${Date.now()}.xls`);
    res.send(csv);
  } catch (error) {
    console.error('Export Excel error:', error);
    res.status(500).json({ error: 'Server error exporting data' });
  }
});

module.exports = router;
