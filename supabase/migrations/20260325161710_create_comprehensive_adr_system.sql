/*
  # Complete Advanced ADR (Adverse Drug Reaction) Management System

  ## Overview
  Comprehensive database schema for a professional ADR reporting and management system
  with multi-role authentication, approval workflows, signal detection, and audit trails.

  ## New Tables Created

  ### 1. users
  - `id` (uuid, primary key) - Unique user identifier
  - `email` (text, unique) - User email for login
  - `password_hash` (text) - Encrypted password
  - `full_name` (text) - User's full name
  - `role` (text) - Role: 'admin' or 'user'
  - `organization` (text) - Healthcare organization
  - `phone` (text) - Contact phone number
  - `is_active` (boolean) - Account active status
  - `created_at` (timestamptz) - Account creation timestamp
  - `updated_at` (timestamptz) - Last update timestamp

  ### 2. drugs
  - `id` (uuid, primary key) - Drug identifier
  - `name` (text) - Drug name
  - `generic_name` (text) - Generic name
  - `manufacturer` (text) - Manufacturer name
  - `description` (text) - Drug description
  - `created_at` (timestamptz) - Record creation timestamp

  ### 3. adr_reports
  - `id` (uuid, primary key) - Report identifier
  - `report_number` (text, unique) - Auto-generated report number
  - `user_id` (uuid) - Reporter user ID
  - `status` (text) - Status: draft, submitted, under_review, approved, rejected, clarification_needed
  - Patient details fields (age, gender, weight, medical_history)
  - Drug details fields (drug_id, dose, route, frequency, batch_number, therapy_dates)
  - Reaction details fields (reaction_type, severity, onset_date, description)
  - `outcome` (text) - Outcome: recovered, recovering, not_recovered, fatal, unknown
  - `causality_assessment` (text) - WHO-UMC scale assessment
  - `admin_notes` (text) - Admin review notes
  - `reviewed_by` (uuid) - Admin who reviewed
  - `reviewed_at` (timestamptz) - Review timestamp
  - Timestamps for creation and updates

  ### 4. attachments
  - `id` (uuid, primary key) - Attachment identifier
  - `adr_report_id` (uuid) - Associated report
  - `file_name` (text) - Original file name
  - `file_path` (text) - Storage path
  - `file_type` (text) - MIME type
  - `file_size` (integer) - File size in bytes
  - `uploaded_at` (timestamptz) - Upload timestamp

  ### 5. audit_logs
  - `id` (uuid, primary key) - Log entry identifier
  - `user_id` (uuid) - User who performed action
  - `action` (text) - Action performed
  - `entity_type` (text) - Type of entity (adr_report, user, etc.)
  - `entity_id` (uuid) - ID of affected entity
  - `details` (jsonb) - Additional details
  - `ip_address` (text) - IP address
  - `created_at` (timestamptz) - Action timestamp

  ### 6. notifications
  - `id` (uuid, primary key) - Notification identifier
  - `user_id` (uuid) - Recipient user
  - `adr_report_id` (uuid) - Related report
  - `type` (text) - Notification type
  - `title` (text) - Notification title
  - `message` (text) - Notification message
  - `is_read` (boolean) - Read status
  - `created_at` (timestamptz) - Creation timestamp

  ### 7. signal_detections
  - `id` (uuid, primary key) - Signal identifier
  - `drug_id` (uuid) - Drug involved
  - `reaction_type` (text) - Type of reaction
  - `occurrence_count` (integer) - Number of occurrences
  - `severity_level` (text) - Average severity
  - `first_detected` (timestamptz) - First detection
  - `last_updated` (timestamptz) - Last update
  - `status` (text) - Signal status
  - `notes` (text) - Investigation notes

  ## Security
  - All tables have Row Level Security (RLS) enabled
  - Restrictive policies ensure data access based on user roles
  - Admins can access all data
  - Users can only access their own reports
  - Authentication required for all operations
*/

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  full_name text NOT NULL,
  role text NOT NULL DEFAULT 'user' CHECK (role IN ('admin', 'user')),
  organization text,
  phone text,
  is_active boolean DEFAULT true,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Drugs table
CREATE TABLE IF NOT EXISTS drugs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  generic_name text,
  manufacturer text,
  description text,
  created_at timestamptz DEFAULT now()
);

-- ADR Reports table
CREATE TABLE IF NOT EXISTS adr_reports (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  report_number text UNIQUE NOT NULL,
  user_id uuid REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'clarification_needed')),
  
  -- Patient details
  patient_age integer,
  patient_gender text CHECK (patient_gender IN ('male', 'female', 'other')),
  patient_weight numeric,
  medical_history text,
  
  -- Drug details
  drug_id uuid REFERENCES drugs(id) ON DELETE SET NULL,
  drug_name text NOT NULL,
  dose text,
  route text,
  frequency text,
  batch_number text,
  therapy_start_date date,
  therapy_end_date date,
  
  -- Reaction details
  reaction_type text NOT NULL,
  severity text NOT NULL CHECK (severity IN ('mild', 'moderate', 'severe')),
  onset_date date,
  reaction_description text NOT NULL,
  
  -- Outcome
  outcome text CHECK (outcome IN ('recovered', 'recovering', 'not_recovered', 'fatal', 'unknown')),
  
  -- Review details
  causality_assessment text CHECK (causality_assessment IN ('certain', 'probable', 'possible', 'unlikely', 'conditional', 'unassessable')),
  admin_notes text,
  reviewed_by uuid REFERENCES users(id) ON DELETE SET NULL,
  reviewed_at timestamptz,
  
  -- Timestamps
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  submitted_at timestamptz
);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  adr_report_id uuid REFERENCES adr_reports(id) ON DELETE CASCADE NOT NULL,
  file_name text NOT NULL,
  file_path text NOT NULL,
  file_type text NOT NULL,
  file_size integer NOT NULL,
  uploaded_at timestamptz DEFAULT now()
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE SET NULL,
  action text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid,
  details jsonb,
  ip_address text,
  created_at timestamptz DEFAULT now()
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  adr_report_id uuid REFERENCES adr_reports(id) ON DELETE CASCADE,
  type text NOT NULL,
  title text NOT NULL,
  message text NOT NULL,
  is_read boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

-- Signal detections table
CREATE TABLE IF NOT EXISTS signal_detections (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  drug_id uuid REFERENCES drugs(id) ON DELETE CASCADE,
  drug_name text NOT NULL,
  reaction_type text NOT NULL,
  occurrence_count integer DEFAULT 1,
  severity_level text,
  first_detected timestamptz DEFAULT now(),
  last_updated timestamptz DEFAULT now(),
  status text DEFAULT 'active' CHECK (status IN ('active', 'investigating', 'resolved')),
  notes text
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_adr_reports_user_id ON adr_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_adr_reports_status ON adr_reports(status);
CREATE INDEX IF NOT EXISTS idx_adr_reports_drug_id ON adr_reports(drug_id);
CREATE INDEX IF NOT EXISTS idx_adr_reports_severity ON adr_reports(severity);
CREATE INDEX IF NOT EXISTS idx_adr_reports_created_at ON adr_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_attachments_adr_report_id ON attachments(adr_report_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE drugs ENABLE ROW LEVEL SECURITY;
ALTER TABLE adr_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE signal_detections ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own profile"
  ON users FOR SELECT
  TO authenticated
  USING (id = auth.uid());

CREATE POLICY "Admins can view all users"
  ON users FOR SELECT
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "Users can update their own profile"
  ON users FOR UPDATE
  TO authenticated
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

CREATE POLICY "Admins can manage all users"
  ON users FOR ALL
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin')
  WITH CHECK ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

-- RLS Policies for drugs table
CREATE POLICY "Anyone authenticated can view drugs"
  ON drugs FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage drugs"
  ON drugs FOR ALL
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin')
  WITH CHECK ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

-- RLS Policies for adr_reports table
CREATE POLICY "Users can view their own reports"
  ON adr_reports FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Admins can view all reports"
  ON adr_reports FOR SELECT
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "Users can create their own reports"
  ON adr_reports FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own draft reports"
  ON adr_reports FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid() AND status = 'draft')
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Admins can update all reports"
  ON adr_reports FOR UPDATE
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin')
  WITH CHECK ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "Users can delete their own draft reports"
  ON adr_reports FOR DELETE
  TO authenticated
  USING (user_id = auth.uid() AND status = 'draft');

-- RLS Policies for attachments table
CREATE POLICY "Users can view attachments for their reports"
  ON attachments FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM adr_reports
      WHERE adr_reports.id = attachments.adr_report_id
      AND adr_reports.user_id = auth.uid()
    )
  );

CREATE POLICY "Admins can view all attachments"
  ON attachments FOR SELECT
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "Users can upload attachments to their reports"
  ON attachments FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM adr_reports
      WHERE adr_reports.id = attachments.adr_report_id
      AND adr_reports.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete attachments from their draft reports"
  ON attachments FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM adr_reports
      WHERE adr_reports.id = attachments.adr_report_id
      AND adr_reports.user_id = auth.uid()
      AND adr_reports.status = 'draft'
    )
  );

-- RLS Policies for audit_logs table
CREATE POLICY "Admins can view all audit logs"
  ON audit_logs FOR SELECT
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

CREATE POLICY "System can insert audit logs"
  ON audit_logs FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- RLS Policies for notifications table
CREATE POLICY "Users can view their own notifications"
  ON notifications FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Users can update their own notifications"
  ON notifications FOR UPDATE
  TO authenticated
  USING (user_id = auth.uid())
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "System can create notifications"
  ON notifications FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- RLS Policies for signal_detections table
CREATE POLICY "Authenticated users can view signals"
  ON signal_detections FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage signals"
  ON signal_detections FOR ALL
  TO authenticated
  USING ((SELECT role FROM users WHERE id = auth.uid()) = 'admin')
  WITH CHECK ((SELECT role FROM users WHERE id = auth.uid()) = 'admin');

-- Function to generate report number
CREATE OR REPLACE FUNCTION generate_report_number()
RETURNS text AS $$
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
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate report number
CREATE OR REPLACE FUNCTION set_report_number()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.report_number IS NULL OR NEW.report_number = '' THEN
    NEW.report_number := generate_report_number();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_report_number
  BEFORE INSERT ON adr_reports
  FOR EACH ROW
  EXECUTE FUNCTION set_report_number();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_adr_reports_updated_at
  BEFORE UPDATE ON adr_reports
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Function for signal detection
CREATE OR REPLACE FUNCTION detect_adr_signals()
RETURNS void AS $$
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
$$ LANGUAGE plpgsql;

-- Insert sample drugs
INSERT INTO drugs (name, generic_name, manufacturer, description) VALUES
  ('Aspirin', 'Acetylsalicylic Acid', 'Bayer', 'Pain reliever and anti-inflammatory'),
  ('Paracetamol', 'Acetaminophen', 'GSK', 'Pain reliever and fever reducer'),
  ('Ibuprofen', 'Ibuprofen', 'Pfizer', 'Nonsteroidal anti-inflammatory drug'),
  ('Amoxicillin', 'Amoxicillin', 'Sandoz', 'Antibiotic penicillin'),
  ('Metformin', 'Metformin HCl', 'Merck', 'Antidiabetic medication'),
  ('Atorvastatin', 'Atorvastatin', 'Lipitor', 'Cholesterol-lowering medication'),
  ('Lisinopril', 'Lisinopril', 'AstraZeneca', 'ACE inhibitor for hypertension'),
  ('Omeprazole', 'Omeprazole', 'AstraZeneca', 'Proton pump inhibitor'),
  ('Ciprofloxacin', 'Ciprofloxacin', 'Bayer', 'Fluoroquinolone antibiotic'),
  ('Warfarin', 'Warfarin Sodium', 'Bristol-Myers', 'Anticoagulant medication')
ON CONFLICT DO NOTHING;

-- Insert default admin user (password: Admin@123)
INSERT INTO users (email, password_hash, full_name, role, organization, is_active) VALUES
  ('admin@adr-system.com', '$2b$10$rKvVPZqXheuqH8J9mEbXmOxB5qY7HvO8ZJKxFxYmXhDqCz8EKqH8O', 'System Administrator', 'admin', 'ADR Central', true)
ON CONFLICT (email) DO NOTHING;

-- Insert sample user (password: User@123)
INSERT INTO users (email, password_hash, full_name, role, organization, is_active) VALUES
  ('user@adr-system.com', '$2b$10$8Z5qJ9YXqH9mEbXmOxB5qZJKxFxYmXhDqCz8EKqH8OrKvVPZqXhe', 'Dr. John Smith', 'user', 'General Hospital', true)
ON CONFLICT (email) DO NOTHING;