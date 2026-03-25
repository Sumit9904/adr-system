const { supabase } = require('../config/database');

const auditLog = (action, entityType) => {
  return async (req, res, next) => {
    const originalJson = res.json;

    res.json = async function(data) {
      if (req.user && res.statusCode < 400) {
        try {
          const logData = {
            user_id: req.user.id,
            action,
            entity_type: entityType,
            entity_id: data?.data?.id || req.params?.id || null,
            details: {
              method: req.method,
              path: req.path,
              body: req.body
            },
            ip_address: req.ip || req.connection.remoteAddress
          };

          await supabase.from('audit_logs').insert(logData);
        } catch (error) {
          console.error('Audit log error:', error);
        }
      }

      originalJson.call(this, data);
    };

    next();
  };
};

module.exports = { auditLog };
