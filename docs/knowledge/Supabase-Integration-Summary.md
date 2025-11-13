# Supabase Integration - Quick Reference

**Status:** Research Complete
**Full Documentation:** `2025-11-04-11-48_Supabase-Integration-Research.md`

---

## TL;DR

**What:** Add Supabase for project persistence while keeping current session_state architecture.

**Why:** Users lose all work when session expires. Need to save projects, track IFC verifications, enable collaboration.

**How:** Hybrid approach - keep df in session_state for speed, auto-save to Supabase for persistence.

**Cost:** Free tier sufficient for MVP (500MB DB, 1GB storage).

**Risk:** Low - non-breaking integration, can rollback easily.

---

## Current State

### Session State Variables
```python
st.session_state = {
    'df': DataFrame,          # All project data (lost on session end)
    'auto_refresh': bool      # UI toggle
}
```

### DataFrame Schema (200-2000 rows typical)
- Original: category, construction_a, operation_b, end_of_life_c, total_gwp
- Suggestions: suggested_scenario, suggested_discipline, suggested_mmi_code
- Mappings: mapped_scenario, mapped_discipline, mapped_mmi_code
- Metadata: is_summary, excluded, row_id

### Current Limitations
- ❌ No persistence between sessions
- ❌ No project organization
- ❌ No IFC verification history
- ❌ No collaboration
- ❌ No audit trail

---

## Proposed Architecture

### Hybrid State Management
```python
st.session_state = {
    # EPHEMERAL (keep as-is)
    'df': DataFrame,              # Working copy
    'auto_refresh': bool,         # UI state
    
    # NEW: Persistence layer
    'project_id': UUID,           # Link to Supabase
    'last_sync': datetime,        # Sync status
    'dirty': bool                 # Has unsaved changes
}
```

### Core Supabase Tables

**projects** (metadata)
- id, name, description, owner_id
- created_at, updated_at, status
- total_rows, mapped_rows, total_gwp (denormalized stats)

**project_data** (actual data)
- project_id, row_id
- category, construction_a, operation_b, end_of_life_c, total_gwp
- suggested_*, mapped_*
- is_summary, excluded

**ifc_files** (future)
- project_id, filename, storage_path
- ifc_schema, total_elements
- processed status

**ifc_verifications** (future)
- ifc_file_id, verified_at
- passed, failed, warnings
- results (JSONB)

---

## Implementation Plan

### Phase 1: MVP Persistence (Week 1)
1. Set up Supabase project
2. Create core tables (projects, project_data)
3. Implement ProjectService
4. Add "Save Project" button to main.py
5. Add "Load Project" sidebar

**Success:** User can save/load projects, no data loss.

### Phase 2: Project Management (Week 2)
6. Project list dashboard
7. Project metadata editing
8. Delete project
9. Search/filter projects

**Success:** Easy multi-project management.

### Phase 3: IFC Integration (Weeks 3-4)
10. IFC upload to Supabase Storage
11. Basic verification (ifcopenshell)
12. Results display
13. Verification history

**Success:** Track IFC quality over time.

### Phase 4: Advanced Features (Week 5+)
14. Mapping templates
15. Audit trail
16. Team collaboration
17. Analytics

---

## Key Code Changes

### New Files
```
utils/supabase_client.py      (~30 lines)   - Client initialization
utils/project_service.py      (~200 lines)  - CRUD operations
pages/5_📁_Projects.py        (~150 lines)  - Project list dashboard
```

### Modified Files
```
main.py                       (+50 lines)   - Save project UI
requirements.txt              (+1 line)     - supabase-py
.env.example                  (+2 lines)    - Supabase config
```

**Total:** ~430 new/modified lines

---

## Data Flow

### Upload Excel
```
1. Parse file → df (memory)
2. Save to Supabase:
   - Create projects record
   - Bulk insert project_data rows
3. Store project_id in session_state
4. User works with df (instant UI)
```

### User Edits
```
1. Edit cell in st.data_editor
2. Update df (memory, instant)
3. Mark dirty = True
4. Background: Auto-save to Supabase (debounced)
5. Update project_data row
6. Mark dirty = False
```

### Load Project
```
1. User selects from "Recent Projects"
2. Fetch project_data rows → df
3. Store in session_state
4. Continue working
```

---

## Critical Decisions

### ✅ Decided

**Authentication:** Start with anonymous mode (no login), add later
**Save Strategy:** Manual "Save Project" button (simple), add auto-save later
**Original Files:** Don't store Excel files (only parsed data)
**IFC Storage:** Supabase Storage (integrated, simple)

### ❓ Open Questions

**Q1:** Auto-save interval? (Recommendation: 3-5 seconds)
**Q2:** Versioning strategy? (Recommendation: Add later if needed)
**Q3:** Conflict resolution? (Recommendation: Last write wins for MVP)

---

## Performance

### Expected Sizes
- Typical project: 200 rows × 150 KB
- Large project: 2,000 rows × 1.5 MB
- IFC file: 2-50 MB

### Free Tier Limits
- Database: 500 MB (~3,300 projects)
- Storage: 1 GB (~20-500 IFC files)
- Bandwidth: 2 GB/month

**Verdict:** Free tier sufficient for 100+ projects/month.

### Optimization
- Cache project lists (5 min TTL)
- Bulk updates (not individual queries)
- Load only needed columns
- Pagination for large projects

---

## Security

### Row-Level Security (RLS)
```sql
-- Users can only access their own projects
CREATE POLICY "Users can view own projects"
ON projects FOR SELECT
USING (auth.uid() = owner_id);
```

### Anonymous Mode (MVP)
```sql
-- All users can access all projects
CREATE POLICY "Public access" ON projects FOR ALL USING (true);
```

**Recommendation:** Anonymous for MVP, add auth for collaboration.

---

## Testing Strategy

### Unit Tests
- ProjectService.create_project()
- ProjectService.load_project()
- ProjectService.update_row()

### Integration Tests
- Full workflow: Upload → Save → Load → Edit → Save
- Data integrity check (df before/after)

### UI Tests
- "Save Project" button works
- "Load Project" sidebar works
- Success/error messages display

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Supabase downtime | Graceful fallback to session-only mode |
| Cost overrun | Monitor usage, set quotas |
| Data loss | Supabase auto-backups, export feature |
| Complexity | Phased rollout, isolate code in services |

---

## Success Metrics

### MVP Success
- ✅ Save project and reload next day
- ✅ Zero data loss on session timeout
- ✅ All existing features work unchanged
- ✅ <100ms save/load overhead

### Full Integration Success
- ✅ Manage 10+ projects easily
- ✅ IFC verification history
- ✅ Templates reduce validation time 50%
- ✅ Team collaboration (5+ users/project)

---

## Next Steps (This Week)

### Day 1: Setup
- [ ] Create Supabase project
- [ ] Get API keys
- [ ] Add to .env
- [ ] Test connection

### Day 2: Schema
- [ ] Create projects table
- [ ] Create project_data table
- [ ] Enable RLS (or public access)
- [ ] Test insert/select

### Day 3: Service Layer
- [ ] Implement supabase_client.py
- [ ] Implement project_service.py
- [ ] Unit tests

### Day 4: UI Integration
- [ ] Add "Save Project" button to main.py
- [ ] Add "Load Project" sidebar
- [ ] Test workflow

### Day 5: Testing & Polish
- [ ] Integration tests
- [ ] Error handling
- [ ] User feedback messages
- [ ] Documentation

---

## Quick Start Code

### Environment Setup
```bash
# .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### Client Initialization
```python
# utils/supabase_client.py
from supabase import create_client
import streamlit as st
import os

@st.cache_resource
def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)
```

### Save Project
```python
# main.py
from utils.project_service import ProjectService

if st.button("💾 Save Project"):
    service = ProjectService()
    project_id = service.create_project(
        name="My Project",
        df=st.session_state['df']
    )
    st.session_state['project_id'] = project_id
    st.success("Project saved!")
```

### Load Project
```python
# main.py sidebar
service = ProjectService()
projects = service.list_projects(limit=10)

selected = st.selectbox(
    "Recent Projects",
    options=[p['id'] for p in projects],
    format_func=lambda id: next(p['name'] for p in projects if p['id'] == id)
)

if selected:
    df = service.load_project(selected)
    st.session_state['df'] = df
    st.session_state['project_id'] = selected
    st.rerun()
```

---

## Resources

- Full Research: `2025-11-04-11-48_Supabase-Integration-Research.md`
- Supabase Docs: https://supabase.com/docs
- Python SDK: https://supabase.com/docs/reference/python
- Row-Level Security: https://supabase.com/docs/guides/auth/row-level-security

---

**Status:** Ready to implement Phase 1 (MVP Persistence)

**Estimated Time:** 1 week (20 hours)

**Dependencies:** Supabase account, API keys, supabase-py package

**Blockers:** None - can start immediately
