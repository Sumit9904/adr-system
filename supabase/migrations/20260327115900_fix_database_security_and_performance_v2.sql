/*
  # Fix Database Security and Performance Issues - Version 2

  ## Overview
  This migration addresses:
  1. Missing indexes on foreign keys
  2. Inefficient RLS policies using auth.uid() directly
  3. Overly permissive RLS policies
  4. Function search path mutability
  5. Multiple permissive policies consolidation
  6. Properly handle function dependencies

  ## Key Improvements
  - Added missing indexes for query performance
  - Optimized all RLS policies with cached auth.uid()
  - Consolidated overlapping policies
  - Fixed overly permissive INSERT policies
  - Fixed function search paths
*/

-- Drop triggers first (dependent on functions)
DROP TRIGGER IF EXISTS trigger_set_report_number ON adr_reports;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_adr_reports_updated_at ON adr_reports;

-- Drop existing functions
DROP FUNCTION IF EXISTS generate_report_number() CASCADE;
DROP FUNCTION IF EXISTS set_report_number() CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DROP FUNCTION IF EXISTS detect_adr_signals() CASCADE;

-- Drop existing RLS policies
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
DROP POLICY IF EXISTS "Admins can view all users" ON users;
DROP POLICY IF EXISTS "Admins can manage all users" ON users;
DROP POLICY IF EXISTS "Users can update their own profile" ON users;
DROP POLICY IF EXISTS "View user data" ON users;
DROP POLICY IF EXISTS "Manage users" ON users;
DROP POLICY IF EXISTS "Admins can create users" ON users;
DROP POLICY IF EXISTS "Admins can delete users" ON users;

DROP POLICY IF EXISTS "Anyone authenticated can view drugs" ON drugs;
DROP POLICY IF EXISTS "Admins can manage drugs" ON drugs;
DROP POLICY IF EXISTS "View drugs" ON drugs;
DROP POLICY IF EXISTS "Manage drugs" ON drugs;
DROP POLICY IF EXISTS "Update drugs" ON drugs;
DROP POLICY IF EXISTS "Delete drugs" ON drugs;

DROP POLICY IF EXISTS "Users can view their own reports" ON adr_reports;
DROP POLICY IF EXISTS "Admins can view all reports" ON adr_reports;
DROP POLICY IF EXISTS "Users can create their own reports" ON adr_reports;
DROP POLICY IF EXISTS "Users can update their own draft reports" ON adr_reports;
DROP POLICY IF EXISTS "Admins can update all reports" ON adr_reports;
DROP POLICY IF EXISTS "Users can delete their own draft reports" ON adr_reports;
DROP POLICY IF EXISTS "View adr reports" ON adr_reports;
DROP POLICY IF EXISTS "Create own adr reports" ON adr_reports;
DROP POLICY IF EXISTS "Update adr reports" ON adr_reports;
DROP POLICY IF EXISTS "Delete own draft adr reports" ON adr_reports;

DROP POLICY IF EXISTS "Users can view attachments for their reports" ON attachments;
DROP POLICY IF EXISTS "Admins can view all attachments" ON attachments;
DROP POLICY IF EXISTS "Users can upload attachments to their reports" ON attachments;
DROP POLICY IF EXISTS "Users can delete attachments from their draft reports" ON attachments;
DROP POLICY IF EXISTS "View attachments" ON attachments;
DROP POLICY IF EXISTS "Upload attachments" ON attachments;
DROP POLICY IF EXISTS "Delete attachments" ON attachments;

DROP POLICY IF EXISTS "Admins can view all audit logs" ON audit_logs;
DROP POLICY IF EXISTS "System can insert audit logs" ON audit_logs;
DROP POLICY IF EXISTS "View audit logs" ON audit_logs;
DROP POLICY IF EXISTS "Insert audit logs" ON audit_logs;

DROP POLICY IF EXISTS "Users can view their own notifications" ON notifications;
DROP POLICY IF EXISTS "Users can update their own notifications" ON notifications;
DROP POLICY IF EXISTS "System can create notifications" ON notifications;
DROP POLICY IF EXISTS "View own notifications" ON notifications;
DROP POLICY IF EXISTS "Update own notifications" ON notifications;
DROP POLICY IF EXISTS "Create notifications" ON notifications;
DROP POLICY IF EXISTS "Delete own notifications" ON notifications;

DROP POLICY IF EXISTS "Authenticated users can view signals" ON signal_detections;
DROP POLICY IF EXISTS "Admins can manage signals" ON signal_detections;
DROP POLICY IF EXISTS "View signals" ON signal_detections;
DROP POLICY IF EXISTS "Manage signals" ON signal_detections;
DROP POLICY IF EXISTS "Update signals" ON signal_detections;
DROP POLICY IF EXISTS "Delete signals" ON signal_detections;

-- ===== ADD MISSING FOREIGN KEY INDEXES =====
CREATE INDEX IF NOT EXISTS idx_adr_reports_reviewed_by ON adr_reports(reviewed_by);
CREATE INDEX IF NOT EXISTS idx_notifications_adr_report_id ON notifications(adr_report_id);
CREATE INDEX IF NOT EXISTS idx_signal_detections_drug_id ON signal_detections(drug_id);

-- ===== RECREATE FUNCTIONS WITH PROPER SEARCH_PATH =====

CREATE FUNCTION generate_report_number()
RETURNS text
LANGUAGE plpgsql
STABLE
SET search_path = public
AS $$
DECLARE
  new_number text;
  year_prefix text;
  sequence_num integer;
BEGIN
  year_prefix := 'ADR' || TO_CHAR(CURRENT_DATE, 'YYYY');
  
  SELECT COUNT(*) + 1 INTO sequence_num
  FROM adr_reports
  WHERE report_number LIKE year_prefix || '%';
  
  new_number := year_prefix || '-' || LPAD(sequence_num::text, 6, '0');
  
  RETURN new_number;
END;
$$;

CREATE FUNCTION set_report_number()
RETURNS TRIGGER
LANGUAGE plpgsql
VOLATILE
SET search_path = public
AS $$
BEGIN
  IF NEW.report_number IS NULL OR NEW.report_number = '' THEN
    NEW.report_number := generate_report_number();
  END IF;
  RETURN NEW;
END;
$$;

CREATE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
VOLATILE
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE FUNCTION detect_adr_signals()
RETURNS void
LANGUAGE plpgsql
VOLATILE
SET search_path = public
AS $$
DECLARE
  signal_record RECORD;
BEGIN
  FOR signal_record IN
    SELECT 
      drug_name,
      reaction_type,
      COUNT(*) as occurrence_count,
      MAX(severity) as max_severity
    FROM adr_reports
    WHERE status = 'approved'
      AND created_at >= NOW() - INTERVAL '90 days'
    GROUP BY drug_name, reaction_type
    HAVING COUNT(*) >= 3
  LOOP
    INSERT INTO signal_detections (drug_name, reaction_type, occurrence_count, severity_level, status)
    VALUES (
      signal_record.drug_name,
      signal_record.reaction_type,
      signal_record.occurrence_count,
      signal_record.max_severity,
      'active'
    )
    ON CONFLICT DO NOTHING;
  END LOOP;
END;
$$;

-- ===== RECREATE TRIGGERS =====

CREATE TRIGGER trigger_set_report_number
  BEFORE INSERT ON adr_reports
  FOR EACH ROW
  EXECUTE FUNCTION set_report_number();

CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_adr_reports_updated_at
  BEFORE UPDATE ON adr_reports
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ===== OPTIMIZED RLS POLICIES WITH CACHED auth.uid() =====

-- Users table
CREATE POLICY "Users can view own profile and admins view all"
  ON users FOR SELECT
  TO authenticated
  USING (
    (id = (SELECT auth.uid())) 
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  );

CREATE POLICY "Users can update own profile and admins can manage"
  ON users FOR UPDATE
  TO authenticated
  USING (
    (id = (SELECT auth.uid())) 
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  )
  WITH CHECK (
    (id = (SELECT auth.uid())) 
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  );

CREATE POLICY "Admins can create users"
  ON users FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Admins can delete users"
  ON users FOR DELETE
  TO authenticated
  USING ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

-- Drugs table
CREATE POLICY "Authenticated users can view drugs"
  ON drugs FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage drugs"
  ON drugs FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Admins can update drugs"
  ON drugs FOR UPDATE
  TO authenticated
  USING ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Admins can delete drugs"
  ON drugs FOR DELETE
  TO authenticated
  USING ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

-- ADR Reports table
CREATE POLICY "Users view own reports and admins view all"
  ON adr_reports FOR SELECT
  TO authenticated
  USING (
    (user_id = (SELECT auth.uid()))
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  );

CREATE POLICY "Users can create their own reports"
  ON adr_reports FOR INSERT
  TO authenticated
  WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own drafts and admins can update all"
  ON adr_reports FOR UPDATE
  TO authenticated
  USING (
    (user_id = (SELECT auth.uid()) AND status = 'draft')
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  )
  WITH CHECK (
    (user_id = (SELECT auth.uid()) AND status = 'draft')
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  );

CREATE POLICY "Users can delete own draft reports"
  ON adr_reports FOR DELETE
  TO authenticated
  USING (
    (user_id = (SELECT auth.uid()) AND status = 'draft')
    OR ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  );

-- Attachments table
CREATE POLICY "Users view attachments for own reports and admins view all"
  ON attachments FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM adr_reports
      WHERE adr_reports.id = attachments.adr_report_id
      AND (
        adr_reports.user_id = (SELECT auth.uid()) 
        OR (SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin'
      )
    )
  );

CREATE POLICY "Users can upload attachments to own reports"
  ON attachments FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM adr_reports
      WHERE adr_reports.id = attachments.adr_report_id
      AND adr_reports.user_id = (SELECT auth.uid())
    )
  );

CREATE POLICY "Users can delete attachments from own draft reports"
  ON attachments FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM adr_reports
      WHERE adr_reports.id = attachments.adr_report_id
      AND adr_reports.user_id = (SELECT auth.uid())
      AND adr_reports.status = 'draft'
    )
  );

-- Audit logs table
CREATE POLICY "Admins can view audit logs"
  ON audit_logs FOR SELECT
  TO authenticated
  USING ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Admins can insert audit logs"
  ON audit_logs FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

-- Notifications table
CREATE POLICY "Users can view own notifications"
  ON notifications FOR SELECT
  TO authenticated
  USING (user_id = (SELECT auth.uid()));

CREATE POLICY "Users can update own notifications"
  ON notifications FOR UPDATE
  TO authenticated
  USING (user_id = (SELECT auth.uid()))
  WITH CHECK (user_id = (SELECT auth.uid()));

CREATE POLICY "Admins can create notifications"
  ON notifications FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Users can delete own notifications"
  ON notifications FOR DELETE
  TO authenticated
  USING (user_id = (SELECT auth.uid()));

-- Signal detections table
CREATE POLICY "Authenticated users can view signals"
  ON signal_detections FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage signals"
  ON signal_detections FOR INSERT
  TO authenticated
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Admins can update signals"
  ON signal_detections FOR UPDATE
  TO authenticated
  USING ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin')
  WITH CHECK ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

CREATE POLICY "Admins can delete signals"
  ON signal_detections FOR DELETE
  TO authenticated
  USING ((SELECT role FROM users WHERE id = (SELECT auth.uid())) = 'admin');

-- ===== VERIFY RLS IS ENABLED =====

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE drugs ENABLE ROW LEVEL SECURITY;
ALTER TABLE adr_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_detections ENABLE ROW LEVEL SECURITY;

-- ===== GRANT PERMISSIONS =====

GRANT EXECUTE ON FUNCTION generate_report_number() TO authenticated, anon;
GRANT EXECUTE ON FUNCTION detect_adr_signals() TO authenticated;

-- ===== UPDATE STATISTICS =====

ANALYZE users;
ANALYZE drugs;
ANALYZE adr_reports;
ANALYZE attachments;
ANALYZE audit_logs;
ANALYZE notifications;
ANALYZE signal_detections;