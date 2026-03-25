const express = require('express');
const { body, validationResult } = require('express-validator');
const { supabase } = require('../config/database');
const { authenticateToken, authorizeRoles } = require('../middleware/auth');
const { auditLog } = require('../middleware/auditLog');
const router = express.Router();

router.get('/', authenticateToken, async (req, res) => {
  try {
    const { search, page = 1, limit = 50 } = req.query;

    let query = supabase
      .from('drugs')
      .select('*', { count: 'exact' });

    if (search) {
      query = query.or(`name.ilike.%${search}%,generic_name.ilike.%${search}%,manufacturer.ilike.%${search}%`);
    }

    const from = (page - 1) * limit;
    const to = from + limit - 1;

    const { data, error, count } = await query
      .order('name', { ascending: true })
      .range(from, to);

    if (error) {
      return res.status(500).json({ error: 'Failed to fetch drugs' });
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
    console.error('Fetch drugs error:', error);
    res.status(500).json({ error: 'Server error fetching drugs' });
  }
});

router.post('/', authenticateToken, authorizeRoles('admin'), [
  body('name').trim().notEmpty(),
  body('generic_name').optional().trim(),
  body('manufacturer').optional().trim(),
  body('description').optional().trim()
], auditLog('CREATE_DRUG', 'drug'), async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { name, generic_name, manufacturer, description } = req.body;

    const { data: drug, error } = await supabase
      .from('drugs')
      .insert({ name, generic_name, manufacturer, description })
      .select()
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to create drug' });
    }

    res.status(201).json({
      success: true,
      data: drug
    });
  } catch (error) {
    console.error('Create drug error:', error);
    res.status(500).json({ error: 'Server error creating drug' });
  }
});

router.put('/:id', authenticateToken, authorizeRoles('admin'), auditLog('UPDATE_DRUG', 'drug'), async (req, res) => {
  try {
    const { name, generic_name, manufacturer, description } = req.body;

    const { data: drug, error } = await supabase
      .from('drugs')
      .update({ name, generic_name, manufacturer, description })
      .eq('id', req.params.id)
      .select()
      .single();

    if (error) {
      return res.status(500).json({ error: 'Failed to update drug' });
    }

    res.json({
      success: true,
      data: drug
    });
  } catch (error) {
    console.error('Update drug error:', error);
    res.status(500).json({ error: 'Server error updating drug' });
  }
});

router.delete('/:id', authenticateToken, authorizeRoles('admin'), auditLog('DELETE_DRUG', 'drug'), async (req, res) => {
  try {
    const { error } = await supabase
      .from('drugs')
      .delete()
      .eq('id', req.params.id);

    if (error) {
      return res.status(500).json({ error: 'Failed to delete drug' });
    }

    res.json({
      success: true,
      message: 'Drug deleted successfully'
    });
  } catch (error) {
    console.error('Delete drug error:', error);
    res.status(500).json({ error: 'Server error deleting drug' });
  }
});

module.exports = router;
