# Report Enhancements - LCA Scenario Mapping

## What's New

The Excel and PDF reports have been completely redesigned to provide **actionable insights** instead of boring data dumps.

## Excel Report Features

### 📊 Sheet 1: Executive Summary
- **Automated insights** from your data
- **Key findings** with color-coded indicators (green/red/yellow)
- **Smart recommendations** based on analysis
- Clear, human-readable summary of what the data means

### 📈 Sheet 2: Scenarios with Chart
- Visual bar chart embedded directly in Excel
- Color-coded headers
- Stacked visualization of LCA phases

### 🔄 Sheet 3: C vs A Comparison
- Smart verdict column: "Stor reduksjon ✓" / "Stor økning ✗"
- Conditional formatting (green = good, red = concern)
- Clear display of differences and ratios

### 🏗️ Sheet 4: MMI Distribution
- Breakdown by scenario showing which MMI codes dominate
- Percentage distribution for easy understanding

### 👷 Sheet 5: Discipline Analysis
- Which disciplines contribute most to emissions
- Formatted for professional presentation

### 📋 Sheet 6: Raw Data
- Clean export of mapped data for further analysis

## PDF Report Features

### Title Page
- Professional layout with key metrics overview
- Generated timestamp

### Executive Summary
- **Automated narrative** explaining what your data shows
- Example: "Scenario C viser en betydelig reduksjon i klimagassutslipp sammenlignet med Scenario A (87.3%, -45,234 kg CO2e)"

### Key Findings Section
- Structured insights table showing:
  - Scenario comparisons
  - Dominant MMI categories
  - Largest contributors by discipline
  - Phase-specific analysis

### Recommendations
- Actionable recommendations based on your data
- Example: If C > A, suggests looking at alternatives
- If mapping < 90%, recommends completing mapping

### Visual Charts (when kaleido installed)
- Embedded stacked bar charts
- Comparison visualizations
- Professional quality for client presentations

### Detailed Analysis
- Scenario comparison with narrative explanation
- MMI breakdown tables per scenario
- All formatted for professional presentation

## Smart Insights Generated

The reports now automatically detect and highlight:

1. **Significant changes**: > 10% difference between scenarios
2. **Dominant patterns**: Which MMI codes or disciplines contribute most
3. **Quality concerns**: Low mapping completeness
4. **Performance verdicts**: Automatic "good/concerning" assessments

## Color Coding

- **Green**: Reductions, good performance
- **Red**: Increases, areas of concern
- **Yellow**: Minor changes, borderline
- **Blue**: Informational highlights

## Installation

To get PDF charts, kaleido has been added to requirements.txt:
```bash
pip install -r requirements.txt
```

Without kaleido, PDFs still work but show text instead of embedded charts.

## Result

Your reports now tell a **story** instead of just showing tables. Perfect for:
- Client presentations
- Internal decision-making
- Documentation of LCA analysis
- Professional deliverables
