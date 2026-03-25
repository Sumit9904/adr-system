const express = require('express');
const { body, validationResult, query } = require('express-validator');
const { supabase } = require('../config/database');
const { authenticateToken, authorizeRoles } = require('../middleware/auth');
const { auditLog } = require('../middleware/auditLog');
const { sendEmail, emailTemplates } = require('../utils/emailService');
const { checkDuplicateReport, getSimilarReports } = require('../utils/signalDetection');
const router = express.Router();

router.post('/', authenticateToken, [
  body('drug_name').trim().notEmpty(),
  body('reaction_type').trim().notEmpty(),
  body('reaction_description').trim().notEmpty(),
  body('severity').isIn(['mild', 'moderate', 'severe']),
  body('patient_age').optional().isInt({ min: 0 }),
  body('status').optional().isIn(['draft', 'submitted'])
], auditLog('CREATE_ADR_REPORT', 'adr_report'), async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const reportData = {
      user_id: req.user.id,
      ...req.body,
      status: req.body.status || 'draft',
      submitted_at: req.body.status === 'submitted' ? new Date().toISOString() : null
    };

    if (reportData.status === 'submitted' && reportData.patient_age) {
      const duplicateCheck = await checkDuplicateReport(
        reportData.drug_name,
        reportData.reaction_type,
        reportData.patient_age,
        req.user.id
      );

      if (duplicateCheck.isDuplicate) {
        return res.status(409).json({
          error: 'Potential duplicate report detected',
          existingReport: duplicateCheck.existingReport,
          message: 'A similar report was submitted recently. Please review before submitting.'
        });
      }
    }

    const { data: report, error } = await supabase
      .from('adr_reports')
      .insert(reportData)
      .select()
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to create report' });
    }

    if (reportData.status === 'submitted') {
      await supabase.from('notifications').insert({
        user_id: req.user.id,
        adr_report_id: report.id,
        type: 'report_submitted',
        title: 'Report Submitted',
        message: `Your ADR report ${report.report_number} has been submitted successfully.`
      });

      const emailData = emailTemplates.reportSubmitted(report.report_number, req.user.full_name);
      await sendEmail({ to: req.user.email, ...emailData });
    }

    res.status(201).json({
      success: true,
      data: report
    });
  } catch (error) {
    console.error('Create report error:', error);
    res.status(500).json({ error: 'Server error creating report' });
  }
});

router.get('/', authenticateToken, [
  query('status').optional().isIn(['draft', 'submitted', 'under_review', 'approved', 'rejected', 'clarification_needed']),
  query('severity').optional().isIn(['mild', 'moderate', 'severe']),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 })
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { status, severity, search, drug_name, date_from, date_to, page = 1, limit = 10 } = req.query;

    let query = supabase
      .from('adr_reports')
      .select('*, users!adr_reports_user_id_fkey(full_name, email, organization)', { count: 'exact' });

    if (req.user.role !== 'admin') {
      query = query.eq('user_id', req.user.id);
    }

    if (status) query = query.eq('status', status);
    if (severity) query = query.eq('severity', severity);
    if (drug_name) query = query.ilike('drug_name', `%${drug_name}%`);
    if (search) {
      query = query.or(`drug_name.ilike.%${search}%,reaction_type.ilike.%${search}%,reaction_description.ilike.%${search}%`);
    }
    if (date_from) query = query.gte('created_at', date_from);
    if (date_to) query = query.lte('created_at', date_to);

    const from = (page - 1) * limit;
    const to = from + limit - 1;

    const { data, error, count } = await query
      .order('created_at', { ascending: false })
      .range(from, to);

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch reports' });
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
    console.error('Fetch reports error:', error);
    res.status(500).json({ error: 'Server error fetching reports' });
  }
});

router.get('/:id', authenticateToken, async (req, res) => {
  try {
    let query = supabase
      .from('adr_reports')
      .select('*, users!adr_reports_user_id_fkey(full_name, email, organization), attachments(*)')
      .eq('id', req.params.id);

    if (req.user.role !== 'admin') {
      query = query.eq('user_id', req.user.id);
    }

    const { data: report, error } = await query.maybeSingle();

    if (error || !report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    res.json({
      success: true,
      data: report
    });
  } catch (error) {
    console.error('Fetch report error:', error);
    res.status(500).json({ error: 'Server error fetching report' });
  }
});

router.put('/:id', authenticateToken, [
  body('status').optional().isIn(['draft', 'submitted'])
], auditLog('UPDATE_ADR_REPORT', 'adr_report'), async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { data: existingReport } = await supabase
      .from('adr_reports')
      .select('status, user_id')
      .eq('id', req.params.id)
      .maybeSingle();

    if (!existingReport) {
      return res.status(404).json({ error: 'Report not found' });
    }

    if (req.user.role !== 'admin' && existingReport.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to update this report' });
    }

    if (req.user.role !== 'admin' && existingReport.status !== 'draft') {
      return res.status(403).json({ error: 'Can only update draft reports' });
    }

    const updateData = { ...req.body };
    if (updateData.status === 'submitted' && existingReport.status === 'draft') {
      updateData.submitted_at = new Date().toISOString();
    }

    const { data: report, error } = await supabase
      .from('adr_reports')
      .update(updateData)
      .eq('id', req.params.id)
      .select()
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to update report' });
    }

    res.json({
      success: true,
      data: report
    });
  } catch (error) {
    console.error('Update report error:', error);
    res.status(500).json({ error: 'Server error updating report' });
  }
});

router.delete('/:id', authenticateToken, auditLog('DELETE_ADR_REPORT', 'adr_report'), async (req, res) => {
  try {
    const { data: existingReport } = await supabase
      .from('adr_reports')
      .select('status, user_id')
      .eq('id', req.params.id)
      .maybeSingle();

    if (!existingReport) {
      return res.status(404).json({ error: 'Report not found' });
    }

    if (req.user.role !== 'admin' && existingReport.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Not authorized to delete this report' });
    }

    if (req.user.role !== 'admin' && existingReport.status !== 'draft') {
      return res.status(403).json({ error: 'Can only delete draft reports' });
    }

    const { error } = await supabase
      .from('adr_reports')
      .delete()
      .eq('id', req.params.id);

    if (error) {
      return res.status(500).json({ error: 'Failed to delete report' });
    }

    res.json({
      success: true,
      message: 'Report deleted successfully'
    });
  } catch (error) {
    console.error('Delete report error:', error);
    res.status(500).json({ error: 'Server error deleting report' });
  }
});

router.put('/:id/review', authenticateToken, authorizeRoles('admin'), [
  body('status').isIn(['under_review', 'approved', 'rejected', 'clarification_needed']),
  body('causality_assessment').optional().isIn(['certain', 'probable', 'possible', 'unlikely', 'conditional', 'unassessable']),
  body('admin_notes').optional().trim()
], auditLog('REVIEW_ADR_REPORT', 'adr_report'), async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { status, causality_assessment, admin_notes } = req.body;

    const { data: report, error: fetchError } = await supabase
      .from('adr_reports')
      .select('*, users!adr_reports_user_id_fkey(full_name, email)')
      .eq('id', req.params.id)
      .maybeSingle();

    if (fetchError || !report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    const { data: updatedReport, error } = await supabase
      .from('adr_reports')
      .update({
        status,
        causality_assessment,
        admin_notes,
        reviewed_by: req.user.id,
        reviewed_at: new Date().toISOString()
      })
      .eq('id', req.params.id)
      .select()
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to update report status' });
    }

    const notificationMessages = {
      approved: 'Your ADR report has been approved',
      rejected: 'Your ADR report has been reviewed',
      clarification_needed: 'Your ADR report requires additional information',
      under_review: 'Your ADR report is under review'
    };

    await supabase.from('notifications').insert({
      user_id: report.user_id,
      adr_report_id: report.id,
      type: `report_${status}`,
      title: `Report ${status.replace('_', ' ')}`,
      message: notificationMessages[status]
    });

    let emailData;
    if (status === 'approved') {
      emailData = emailTemplates.reportApproved(report.report_number, report.users.full_name);
    } else if (status === 'rejected') {
      emailData = emailTemplates.reportRejected(report.report_number, report.users.full_name, admin_notes || 'No reason provided');
    } else if (status === 'clarification_needed') {
      emailData = emailTemplates.clarificationNeeded(report.report_number, report.users.full_name, admin_notes || 'Additional information required');
    }

    if (emailData) {
      await sendEmail({ to: report.users.email, ...emailData });
    }

    res.json({
      success: true,
      data: updatedReport
    });
  } catch (error) {
    console.error('Review report error:', error);
    res.status(500).json({ error: 'Server error reviewing report' });
  }
});

router.get('/:id/similar', authenticateToken, async (req, res) => {
  try {
    const { data: report } = await supabase
      .from('adr_reports')
      .select('drug_name, reaction_type')
      .eq('id', req.params.id)
      .maybeSingle();

    if (!report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    const result = await getSimilarReports(report.drug_name, report.reaction_type);

    res.json({
      success: true,
      data: result.data || []
    });
  } catch (error) {
    console.error('Similar reports error:', error);
    res.status(500).json({ error: 'Server error fetching similar reports' });
  }
});

module.exports = router;
