# Data Directory

## Structure

- **`raw/`** - Original, immutable data from Reduzer exports (gitignored)
- **`processed/`** - Cleaned, transformed data ready for analysis (gitignored)
- **`samples/`** - Small sample files for testing and development (committed)

## Data Sources

### Reduzer Exports
- **Format**: Excel (.xlsx)
- **Required columns**:
  - `category` or first column: Text with Scenario/Discipline/MMI patterns
  - `Construction (A)`: Construction phase GWP (kg CO2e)
  - `Operation (B)`: Operation phase GWP (kg CO2e)
  - `End-of-life (C)`: End-of-life phase GWP (kg CO2e)

### Expected Patterns in Category Column
- **Scenarios**: A, B, C, or D
- **Disciplines**: RIV, ARK, RIE, RIB, RIBp
- **MMI Codes**: 300, 700, 800, 900
- **Examples**:
  - "Scenario A - RIV - MMI300"
  - "Scenario C - ARK - MMI 700"
  - "A - Scenario B - RIE - Nybygg"

### Summary Rows (Auto-excluded)
Rows containing these patterns are automatically marked for exclusion:
- "RAMBELL" or "RAMBOELL"
- "S8 -", "S10 -" (S-prefixed summaries)
- "Total", "Sum", "Totalt"

## Usage

### Raw Data
1. Place original Reduzer exports in `data/raw/`
2. Never modify files in `raw/` - keep originals intact
3. Files in `raw/` are gitignored

### Processed Data
1. Application processes data in-memory
2. For batch processing, save cleaned data to `data/processed/`
3. Files in `processed/` are gitignored

### Sample Data
1. Place small test files in `data/samples/`
2. Sample files ARE committed to git
3. Use for development and testing
4. Keep files small (<100 KB)

## Data Validation

Valid Excel files must:
- ✅ Have a category column (any name, typically first column)
- ✅ Have LCA phase columns (Construction/Operation/End-of-life)
- ✅ Contain numeric GWP values (kg CO2e)
- ✅ Have at least one row of data

## Privacy & Security

- ❌ Never commit actual project data to git
- ❌ Never commit files with client information
- ✅ Only commit anonymized samples
- ✅ Use generic category names in samples

## Adding Sample Data

```bash
# Create a small sample file for testing
cp data/raw/project_data.xlsx data/samples/sample_simple.xlsx

# Edit to anonymize and reduce size
# Remove sensitive data
# Keep only ~20 rows
# Generic category names
```

## Questions?

See:
- `docs/knowledge/Architecture.md` - Data processing flow
- `utils/data_parser.py` - Excel loading logic
- `utils/detector.py` - Pattern recognition rules
