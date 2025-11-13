-- ============================================
-- LCA Scenario Mapping - Supabase Schema
-- ============================================
-- Run this in your Supabase SQL Editor to set up the database
-- https://supabase.com/dashboard/project/_/sql

-- ============================================
-- 1. PROJECTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),

  -- Optional: Link to auth.users when authentication is added
  owner_id UUID,  -- REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Cached statistics for performance
  total_rows INTEGER DEFAULT 0,
  mapped_rows INTEGER DEFAULT 0,
  total_gwp NUMERIC DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_projects_updated ON projects(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ============================================
-- 2. PROJECT_DATA TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS project_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  row_id INTEGER NOT NULL,

  -- Original Excel data
  category TEXT,
  construction_a NUMERIC DEFAULT 0,
  operation_b NUMERIC DEFAULT 0,
  end_of_life_c NUMERIC DEFAULT 0,
  total_gwp NUMERIC DEFAULT 0,

  -- AI suggestions
  suggested_scenario TEXT,
  suggested_discipline TEXT,
  suggested_mmi_code TEXT,
  suggested_mmi_label TEXT,

  -- User mappings (the valuable data!)
  mapped_scenario TEXT,
  mapped_discipline TEXT,
  mapped_mmi_code TEXT,

  -- Flags
  is_summary BOOLEAN DEFAULT FALSE,
  excluded BOOLEAN DEFAULT FALSE,

  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure unique row_id per project
  UNIQUE(project_id, row_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_project_data_project ON project_data(project_id);
CREATE INDEX IF NOT EXISTS idx_project_data_row ON project_data(project_id, row_id);

-- ============================================
-- 3. IFC_FILES TABLE (Future - for IFC integration)
-- ============================================
CREATE TABLE IF NOT EXISTS ifc_files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

  filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,  -- Supabase Storage bucket path
  file_size_bytes BIGINT,

  -- IFC metadata
  ifc_schema TEXT,  -- IFC2X3, IFC4, etc.
  total_elements INTEGER,

  -- Processing status
  processed BOOLEAN DEFAULT FALSE,
  processing_error TEXT,

  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ifc_files_project ON ifc_files(project_id);

-- ============================================
-- 4. IFC_VERIFICATIONS TABLE (Future)
-- ============================================
CREATE TABLE IF NOT EXISTS ifc_verifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ifc_file_id UUID NOT NULL REFERENCES ifc_files(id) ON DELETE CASCADE,

  verified_at TIMESTAMPTZ DEFAULT NOW(),
  verified_by UUID,  -- Optional: auth.users reference

  -- Summary counts
  passed INTEGER DEFAULT 0,
  failed INTEGER DEFAULT 0,
  warnings INTEGER DEFAULT 0,

  -- Detailed results stored as JSONB for flexibility
  results JSONB,

  -- Example results structure:
  -- {
  --   "duplicate_guids": [...],
  --   "ark_rib_overlaps": [...],
  --   "material_issues": [...]
  -- }
);

CREATE INDEX IF NOT EXISTS idx_ifc_verifications_file ON ifc_verifications(ifc_file_id);

-- ============================================
-- 5. FUNCTIONS: Auto-update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to projects table
DROP TRIGGER IF EXISTS update_projects_updated_at ON projects;
CREATE TRIGGER update_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Apply to project_data table
DROP TRIGGER IF EXISTS update_project_data_updated_at ON project_data;
CREATE TRIGGER update_project_data_updated_at
  BEFORE UPDATE ON project_data
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================
-- Note: These are disabled by default for MVP (anonymous access)
-- Enable when adding authentication

-- Enable RLS (commented out for MVP)
-- ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE project_data ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ifc_files ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ifc_verifications ENABLE ROW LEVEL SECURITY;

-- Example policies (commented out for MVP):
--
-- -- Users can only see their own projects
-- CREATE POLICY "Users can view own projects"
--   ON projects FOR SELECT
--   USING (auth.uid() = owner_id);
--
-- -- Users can create projects
-- CREATE POLICY "Users can create projects"
--   ON projects FOR INSERT
--   WITH CHECK (auth.uid() = owner_id);
--
-- -- Users can update own projects
-- CREATE POLICY "Users can update own projects"
--   ON projects FOR UPDATE
--   USING (auth.uid() = owner_id);
--
-- -- Users can delete own projects
-- CREATE POLICY "Users can delete own projects"
--   ON projects FOR DELETE
--   USING (auth.uid() = owner_id);

-- ============================================
-- 7. STORAGE BUCKETS (for IFC files)
-- ============================================
-- Run this in Supabase Dashboard > Storage, or via SQL:

-- INSERT INTO storage.buckets (id, name, public)
-- VALUES ('ifc-files', 'ifc-files', false);

-- Storage policies (when authentication added):
--
-- CREATE POLICY "Users can upload IFC files"
--   ON storage.objects FOR INSERT
--   WITH CHECK (bucket_id = 'ifc-files' AND auth.uid() IS NOT NULL);
--
-- CREATE POLICY "Users can view own IFC files"
--   ON storage.objects FOR SELECT
--   USING (bucket_id = 'ifc-files' AND auth.uid() IS NOT NULL);

-- ============================================
-- 8. VERIFICATION
-- ============================================
-- After running this schema, verify tables were created:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- ORDER BY table_name;

-- Check indexes:
-- SELECT indexname FROM pg_indexes
-- WHERE schemaname = 'public'
-- ORDER BY indexname;
