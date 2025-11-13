# Project Restructure - November 4, 2025

## Changes Made

### Directory Structure
- Created `docs/` with required subdirectories:
  - `/worklog` - Development session notes
  - `/plans` - Planning documents
  - `/research` - Research and investigations
  - `/todos` - Task tracking
  - `/knowledge` - Architecture and domain knowledge

### File Organization
- Moved `REPORT_ENHANCEMENTS.md` → `docs/knowledge/`
- Moved `versions/` → `docs/knowledge/versions/`
- Moved `reduzer.zip` → `data/raw/` (corrected: it's data, not docs)
- Created `.env.example`, `.gitignore`
- Created `docs/knowledge/Architecture.md`
- Created `docs/knowledge/Project-Structure.md`
- Kept root clean: only main.py, utils/, requirements.txt, README.md, CLAUDE.md

### CLAUDE.md Update
Rewrote to follow dev standards:
- **Short and sweet** - Reduced from ~250 lines to ~140 lines
- **Focus on decisions** - Emphasized architectural choices, not implementation details
- **Cross-session context** - Quick reference for future sessions
- **References detailed docs** - Points to `docs/knowledge/` instead of duplicating
- **Error handling philosophy** - Added explicit "fail loudly" guidance

### Structure Rationale
Following `/home/edkjo/dev/.claude.md` guidelines for consistent project organization across the dev directory.

Key principle: "Keep it short and sweet - Don't write just to write; conserve tokens"

Streamlit convention keeps main.py in root for easy `streamlit run main.py` execution.

## New Features Added Today
- **Discipline-level analysis**: Within-scenario and cross-scenario discipline tracking
- Functions: `get_discipline_contribution()`, `compare_disciplines_across_scenarios()`, `get_all_disciplines_comparison()`
- Visualizations: Pie charts, grouped bars, cross-scenario comparisons
- UI: Two-tab interface for discipline analysis

## Decisions Made

### Why exclude vs delete?
Preserves data integrity. Users can re-include if needed. No data loss.

### Why suggestions vs mappings?
Auto-detection isn't perfect. Give users control. Prevent silent errors from regex mismatches.

### Why live updates?
Trade-off: Slightly slower but ensures UI consistency. Better UX than stale data.

## Completed
✅ Documentation structure
✅ Clean root directory
✅ .env.example and .gitignore
✅ Concise CLAUDE.md
✅ Knowledge base setup
✅ Worklog system
