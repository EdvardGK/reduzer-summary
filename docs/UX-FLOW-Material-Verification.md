# Material Verification - UX Flow

## Design Philosophy

**Goal:** Simple, clear 3-step process
**Users:** LCA analysts who need quick verification
**Key metric:** PASS/FAIL verdict (deviation ≤5%)

---

## Information Architecture

```
┌─────────────────────────────────────────┐
│  HEADER                                 │
│  - Title                                │
│  - One-line explanation                 │
│  - Acceptance criteria (≤5%)            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  STEP 1: INPUT                          │
│  ┌───────────────┐  ┌─────────────┐   │
│  │ File Upload   │  │ Resources   │   │
│  │ (prominent)   │  │ - Template  │   │
│  └───────────────┘  │ - Example   │   │
│                     │ - Guide     │   │
│                     └─────────────┘   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  WELCOME SCREEN (no data)               │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ What it does │  │ What you need│   │
│  │ (explanation)│  │ (requirements)│   │
│  └──────────────┘  └──────────────┘   │
│  [Template preview expandable]          │
└─────────────────────────────────────────┘

              ↓ (after upload)

┌─────────────────────────────────────────┐
│  STEP 2: OUTPUT (VERDICT)               │
│  ┌─────────────────────────────────┐   │
│  │  ✅ PASS  or  ❌ FAIL           │   │
│  │  (large, colored, unmistakable) │   │
│  └─────────────────────────────────┘   │
│  ┌──────┐┌──────┐┌──────┐┌──────┐     │
│  │ Qty A││ Qty C││ Δ abs││  Δ % │     │
│  └──────┘└──────┘└──────┘└──────┘     │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  MMI DISTRIBUTION (Scenario C)          │
│  ┌─────────┐┌─────────┐┌─────────┐    │
│  │ MMI 300 ││ MMI 700 ││ MMI 800 │    │
│  │ (New)   ││ (Kept)  ││ (Reused)│    │
│  └─────────┘└─────────┘└─────────┘    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  PROBLEMS (if FAIL)                     │
│  ⚠️ X elements need review              │
│  [Table: Top 10 worst deviations]      │
│  [Expandable: Common causes & fixes]   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  DETAILS (collapsible)                  │
│  ▶ Full comparison (all objects)        │
│    - Discipline summary                 │
│    - Object-by-object table             │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  VISUALIZATIONS (collapsible)           │
│  ▶ See charts                           │
│    - Discipline comparison              │
│    - MMI distribution pie               │
│    - Deviation bar chart                │
│    - MMI breakdown stacked              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  STEP 3: EXPORT                         │
│  ┌──────────────────┐┌──────────────┐  │
│  │ 📊 Excel Report  ││ 📄 Raw CSV   │  │
│  └──────────────────┘└──────────────┘  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  ACTIONS                                │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │🔄 Upload New │  │ Status: PASS/FAIL│ │
│  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────┘
```

---

## I/O Strategy

### INPUT
**Format:** CSV or Excel
**Required columns:** 6 (Object Type, Discipline, Scenario, MMI Category, Quantity, Unit)
**Optional columns:** 3 (IFC Class, Description, Notes)
**Validation:** Real-time on upload with clear error messages

### OUTPUT
**Primary:** PASS/FAIL verdict (immediate, large, colored)
**Secondary:**
- 4 metric cards (totals, deviation)
- MMI distribution (3 cards)
- Problem list (if FAIL)
- Excel report (downloadable)

---

## User Journey

### Happy Path (PASS)
```
1. User uploads file
   ↓
2. Sees green "✅ PASS" immediately
   ↓
3. Reviews metrics (all within tolerance)
   ↓
4. Downloads report (optional)
   ↓
5. Continues with LCA analysis
```
**Time:** 2 minutes

### Error Path (FAIL)
```
1. User uploads file
   ↓
2. Sees red "❌ FAIL" immediately
   ↓
3. Scrolls to "Elementer som trenger gjennomgang"
   ↓
4. Sees top 10 worst deviations in table
   ↓
5. Expands "Vanlige årsaker til avvik"
   ↓
6. Identifies issue (e.g., unit mismatch)
   ↓
7. Fixes data in original file
   ↓
8. Clicks "🔄 Last opp ny fil"
   ↓
9. Uploads corrected file
   ↓
10. Sees "✅ PASS"
```
**Time:** 10-15 minutes (including fix)

### First-Time User
```
1. Arrives at page (no file)
   ↓
2. Sees "Steg 1: Last opp data"
   ↓
3. Reads "Hva dette gjør" (left column)
   ↓
4. Reviews "Hva du trenger" (right column)
   ↓
5. Clicks "Blank template" link
   ↓
6. Downloads template
   ↓
7. Expands "Forhåndsvisning av template"
   ↓
8. Sees example data
   ↓
9. Fills in template with own data
   ↓
10. Uploads and continues...
```
**Time:** 30 minutes (first time)

---

## Visual Hierarchy

### Priority 1 (Always Visible)
- Upload button
- Verdict (PASS/FAIL)
- Key metrics (4 cards)
- Resource links

### Priority 2 (Visible if Relevant)
- Problem list (only if FAIL)
- MMI distribution (always after upload)
- Export buttons

### Priority 3 (User-Initiated)
- Full comparison table (expandable)
- Visualizations (expandable)
- Troubleshooting tips (expandable)

---

## Color System

### Status Colors
- **Green** (success): PASS verdict, metrics within tolerance
- **Red** (error): FAIL verdict, validation errors
- **Yellow** (warning): Flagged items, needs review
- **Blue** (info): Help text, resources

### Element Colors
- **MMI 300** (New): #FFD93D (yellow)
- **MMI 700** (Kept): #6BCF7F (green)
- **MMI 800** (Reused): #4D96FF (blue)

---

## Typography

### Hierarchy
```
H1 (Title): 📊 Material-Verifisering
H2 (Section): ### 🎯 Steg 2: Resultat
H3 (Subsection): #### Sammenligning per Disiplin
Body: Regular text, code blocks
Emphasis: **Bold** for key terms
```

### Font Sizes (via Streamlit defaults)
- Verdict: Extra large (CSS: 2.5rem)
- Metrics: Large (st.metric)
- Headers: Medium (###)
- Body: Regular (markdown)

---

## Interaction Patterns

### File Upload
```
[Drag & drop area or Browse button]
↓
[Spinner: "Behandler data..."]
↓
[Success: "✅ Data lastet - X rader"]
OR
[Error: "⚠️ Valideringsfeil funnet"]
```

### Expandable Sections
```
▶ Se fullstendig sammenligning (alle objekter)
[Click to expand]
↓
▼ Se fullstendig sammenligning (alle objekter)
  [Content appears]
  [Tables, charts, etc.]
```

### Download Buttons
```
[📊 Excel-rapport]  [📄 Rå-data (CSV)]
↓ (on click)
[Browser download dialog]
```

---

## Responsive Behavior

### Desktop (>1200px)
- 2-column layout for welcome screen
- 4-column layout for metrics
- Full-width tables and charts

### Tablet (768-1200px)
- 2-column layout maintained
- Metrics stack to 2x2 grid
- Tables scroll horizontally

### Mobile (<768px)
- Single column layout
- Metrics stack vertically
- Upload area full-width
- Tables with horizontal scroll

---

## Accessibility

### Color Contrast
- Green/Red text on white: 4.5:1+ ratio
- Status indicators include text + emoji
- Never rely on color alone

### Navigation
- Keyboard accessible (tab order)
- Screen reader friendly (semantic HTML)
- Clear labels for all inputs

### Error Messages
- Specific, actionable
- Appear immediately
- Include solution steps

---

## Performance

### Load Time
- Initial page: <1s
- File upload: 2-5s (depends on size)
- Chart generation: 1-2s (lazy load)

### File Size Limits
- CSV: Up to 50 MB
- Excel: Up to 25 MB
- Rows: Up to 100,000

### Caching
- Session state for metrics
- No re-calculation on UI interactions
- Charts generated on-demand (expandable)

---

## Error Handling

### Validation Errors (Upload)
```
⚠️ Valideringsfeil funnet
• Invalid disciplines found: Architect. Valid: ARK, RIV, ...
• Scenario A must only use MMI 300
• Inconsistent units for: Interior walls
```
**User action:** Fix and re-upload

### Calculation Errors (Rare)
```
❌ Kunne ikke beregne metrikker
```
**User action:** Check data format, contact support

### File Format Errors
```
❌ Kunne ikke laste fil: Unsupported format
```
**User action:** Convert to CSV or Excel

---

## Success Metrics (for UX evaluation)

### Primary
- **Task completion rate**: % users who get PASS/FAIL verdict
- **Time to verdict**: Seconds from upload to seeing result
- **Error recovery rate**: % users who fix FAIL → PASS

### Secondary
- **Help access rate**: % users who click template/guide links
- **Report download rate**: % users who export Excel report
- **Re-upload rate**: Average attempts before PASS

---

## Future Enhancements

### Short-term
- [ ] Drag & drop anywhere on page
- [ ] Progress indicator for large files
- [ ] Export to PDF option

### Medium-term
- [ ] Direct IFC file upload (auto-extract quantities)
- [ ] Unit conversion helper (mm2 → m2)
- [ ] Pre-flight check before full calculation

### Long-term
- [ ] AI-assisted data mapping
- [ ] Historical deviation tracking
- [ ] Multi-project comparison
- [ ] Real-time collaboration
