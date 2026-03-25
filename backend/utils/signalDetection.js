const { supabase } = require('../config/database');

const detectSignals = async () => {
  try {
    const { data, error } = await supabase.rpc('detect_adr_signals');

    if (error) throw error;

    return { success: true, message: 'Signal detection completed' };
  } catch (error) {
    console.error('Signal detection error:', error);
    return { success: false, error: error.message };
  }
};

const checkDuplicateReport = async (drugName, reactionType, patientAge, userId) => {
  try {
    const { data, error } = await supabase
      .from('adr_reports')
      .select('id, report_number, created_at')
      .eq('user_id', userId)
      .ilike('drug_name', drugName)
      .ilike('reaction_type', reactionType)
      .eq('patient_age', patientAge)
      .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())
      .order('created_at', { ascending: false })
      .limit(1);

    if (error) throw error;

    return {
      isDuplicate: data && data.length > 0,
      existingReport: data && data.length > 0 ? data[0] : null
    };
  } catch (error) {
    console.error('Duplicate check error:', error);
    return { isDuplicate: false, error: error.message };
  }
};

const getSimilarReports = async (drugName, reactionType, limit = 5) => {
  try {
    const { data, error } = await supabase
      .from('adr_reports')
      .select('id, report_number, drug_name, reaction_type, severity, created_at')
      .or(`drug_name.ilike.%${drugName}%,reaction_type.ilike.%${reactionType}%`)
      .eq('status', 'approved')
      .order('created_at', { ascending: false })
      .limit(limit);

    if (error) throw error;

    return { success: true, data };
  } catch (error) {
    console.error('Similar reports error:', error);
    return { success: false, error: error.message };
  }
};

module.exports = {
  detectSignals,
  checkDuplicateReport,
  getSimilarReports
};
