# -*- coding: utf-8 -*-
"""
Report generation for LCA Scenario Mapping
Generates Excel and PDF reports
"""

import io
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
import plotly.graph_objects as go


# ==============================================================================
# EXCEL EXPORT
# ==============================================================================

def generate_excel_report(df: pd.DataFrame, structure: Dict[str, Any],
                         scenario_summary: pd.DataFrame) -> io.BytesIO:
    """
    Generate comprehensive Excel report with multiple sheets.

    Args:
        df: Full dataframe with mapping
        structure: Aggregated hierarchical structure
        scenario_summary: Summary dataframe

    Returns:
        BytesIO object with Excel file
    """
    excel_output = io.BytesIO()

    with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
        # Sheet 1: Metadata
        metadata = pd.DataFrame({
            'Felt': [
                'Rapport',
                'Generert',
                'Total rader',
                'Kartlagte rader',
                'Ekskluderte rader'
            ],
            'Verdi': [
                'LCA Scenario Mapping',
                datetime.now().strftime('%d.%m.%Y %H:%M'),
                len(df),
                len(df[~df['excluded'] & df['mapped_scenario'].notna()]),
                df['excluded'].sum()
            ]
        })
        metadata.to_excel(writer, sheet_name='Rapportinfo', index=False)

        # Sheet 2: Scenario Summary
        scenario_summary.to_excel(writer, sheet_name='Scenario-oppsummering', index=False)

        # Sheet 3: Scenario C vs A Comparison
        if 'C' in structure and 'A' in structure:
            from .data_parser import compare_scenarios
            comparison = compare_scenarios(structure, 'A', 'C')

            if comparison:
                comp_data = []
                for key, label in [
                    ('construction_a', 'Konstruksjon (A)'),
                    ('operation_b', 'Drift (B)'),
                    ('end_of_life_c', 'Avslutning (C)'),
                    ('total_gwp', 'Total GWP')
                ]:
                    base_val = structure['A']['total'][key]
                    comp_val = structure['C']['total'][key]
                    diff = comparison['difference'][key]
                    ratio = comparison['ratio'][key] if comparison['ratio'][key] else 0

                    comp_data.append({
                        'LCA-fase': label,
                        'Scenario A': base_val,
                        'Scenario C': comp_val,
                        'Differanse (C-A)': diff,
                        'Ratio (C/A) %': ratio
                    })

                comp_df = pd.DataFrame(comp_data)
                comp_df.to_excel(writer, sheet_name='C vs A Sammenligning', index=False)

        # Sheet 4: Discipline Breakdown per Scenario
        discipline_data = []
        for scenario, scenario_data in structure.items():
            for discipline, disc_data in scenario_data['disciplines'].items():
                discipline_data.append({
                    'Scenario': scenario,
                    'Disiplin': discipline,
                    'Konstruksjon (A)': disc_data['total']['construction_a'],
                    'Drift (B)': disc_data['total']['operation_b'],
                    'Avslutning (C)': disc_data['total']['end_of_life_c'],
                    'Total GWP': disc_data['total']['total_gwp'],
                    'Antall rader': disc_data['total']['count']
                })

        if discipline_data:
            disc_df = pd.DataFrame(discipline_data)
            disc_df.to_excel(writer, sheet_name='Disipliner', index=False)

        # Sheet 5: MMI Breakdown
        mmi_data = []
        for scenario, scenario_data in structure.items():
            for discipline, disc_data in scenario_data['disciplines'].items():
                for mmi_code, mmi_info in disc_data['mmi_categories'].items():
                    mmi_data.append({
                        'Scenario': scenario,
                        'Disiplin': discipline,
                        'MMI': mmi_code,
                        'MMI Status': mmi_info['label'],
                        'Konstruksjon (A)': mmi_info['construction_a'],
                        'Drift (B)': mmi_info['operation_b'],
                        'Avslutning (C)': mmi_info['end_of_life_c'],
                        'Total GWP': mmi_info['total_gwp'],
                        'Antall rader': mmi_info['count']
                    })

        if mmi_data:
            mmi_df = pd.DataFrame(mmi_data)
            mmi_df.to_excel(writer, sheet_name='MMI Detaljer', index=False)

        # Sheet 5b: MMI Distribution per Scenario
        from .visualizations import get_mmi_summary_stats
        mmi_dist_data = []
        for scenario in structure.keys():
            mmi_stats = get_mmi_summary_stats(structure, scenario)
            if not mmi_stats.empty:
                mmi_stats['Scenario'] = scenario
                mmi_dist_data.append(mmi_stats)

        if mmi_dist_data:
            mmi_dist_df = pd.concat(mmi_dist_data, ignore_index=True)
            # Reorder columns
            mmi_dist_df = mmi_dist_df[['Scenario', 'MMI', 'Status', 'GWP (kg CO2e)', 'Andel (%)', 'Antall rader']]
            mmi_dist_df.to_excel(writer, sheet_name='MMI Fordeling', index=False)

        # Sheet 6: Kartlagt data (only active rows)
        active_df = df[~df['excluded'] & df['mapped_scenario'].notna()].copy()
        export_cols = [
            'category', 'mapped_scenario', 'mapped_discipline', 'mapped_mmi_code',
            'construction_a', 'operation_b', 'end_of_life_c', 'total_gwp'
        ]
        active_export = active_df[export_cols].rename(columns={
            'category': 'Kategori',
            'mapped_scenario': 'Scenario',
            'mapped_discipline': 'Disiplin',
            'mapped_mmi_code': 'MMI',
            'construction_a': 'Konstruksjon (A)',
            'operation_b': 'Drift (B)',
            'end_of_life_c': 'Avslutning (C)',
            'total_gwp': 'Total GWP'
        })
        active_export.to_excel(writer, sheet_name='Kartlagt data', index=False)

        # Sheet 7: Full data (including excluded)
        full_export_cols = [
            'category', 'mapped_scenario', 'mapped_discipline', 'mapped_mmi_code',
            'construction_a', 'operation_b', 'end_of_life_c', 'total_gwp', 'excluded'
        ]
        full_export = df[full_export_cols].rename(columns={
            'category': 'Kategori',
            'mapped_scenario': 'Scenario',
            'mapped_discipline': 'Disiplin',
            'mapped_mmi_code': 'MMI',
            'construction_a': 'Konstruksjon (A)',
            'operation_b': 'Drift (B)',
            'end_of_life_c': 'Avslutning (C)',
            'total_gwp': 'Total GWP',
            'excluded': 'Ekskludert'
        })
        full_export.to_excel(writer, sheet_name='Alle data', index=False)

    excel_output.seek(0)
    return excel_output


# ==============================================================================
# PDF REPORT
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    """Canvas with page numbers"""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page_num = self._pageNumber
        text = f"Side {page_num} av {page_count}"
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.grey)
        self.drawRightString(A4[0] - 2*cm, 1*cm, text)
        self.drawString(2*cm, 1*cm, f"Generert: {datetime.now().strftime('%d.%m.%Y')}")


def generate_pdf_report(df: pd.DataFrame, structure: Dict[str, Any],
                       scenario_summary: pd.DataFrame) -> io.BytesIO:
    """
    Generate PDF report with key metrics and charts.

    Args:
        df: Full dataframe
        structure: Aggregated structure
        scenario_summary: Summary dataframe

    Returns:
        BytesIO object with PDF file
    """
    pdf_output = io.BytesIO()
    doc = SimpleDocTemplate(pdf_output, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1565C0'),
        alignment=TA_CENTER,
        spaceAfter=30
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1565C0'),
        spaceBefore=20,
        spaceAfter=10
    )

    # Title
    elements.append(Paragraph("LCA Scenario Mapping Rapport", title_style))
    elements.append(Paragraph(
        f"Generert: {datetime.now().strftime('%d.%m.%Y kl. %H:%M')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 1*cm))

    # Key metrics
    elements.append(Paragraph("Hovedn�kkeltall", heading_style))

    stats_data = [
        ['Total rader', str(len(df))],
        ['Kartlagte rader', str(len(df[~df['excluded'] & df['mapped_scenario'].notna()]))],
        ['Ekskluderte rader', str(int(df['excluded'].sum()))],
        ['Antall scenarioer', str(len(structure))]
    ]

    stats_table = Table(stats_data, colWidths=[8*cm, 6*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 1*cm))

    # Scenario Summary
    elements.append(Paragraph("Scenario-oppsummering", heading_style))

    scenario_table_data = [['Scenario', 'Konstr. (A)', 'Drift (B)', 'Avsl. (C)', 'Total GWP']]
    for _, row in scenario_summary.iterrows():
        scenario_table_data.append([
            row['Scenario'],
            f"{row['Konstruksjon (A)']:,.0f}",
            f"{row['Drift (B)']:,.0f}",
            f"{row['Avslutning (C)']:,.0f}",
            f"{row['Total GWP']:,.0f}"
        ])

    scenario_table = Table(scenario_table_data, colWidths=[2*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(scenario_table)
    elements.append(Spacer(1, 1*cm))

    # Scenario C vs A (if both exist)
    if 'C' in structure and 'A' in structure:
        from .data_parser import compare_scenarios
        comparison = compare_scenarios(structure, 'A', 'C')

        if comparison:
            elements.append(PageBreak())
            elements.append(Paragraph("Scenario C vs A Sammenligning", heading_style))

            comp_table_data = [['LCA-fase', 'Scenario A', 'Scenario C', 'Differanse', 'Ratio %']]
            for key, label in [
                ('total_gwp', 'Total GWP'),
                ('construction_a', 'Konstruksjon (A)'),
                ('operation_b', 'Drift (B)'),
                ('end_of_life_c', 'Avslutning (C)')
            ]:
                base_val = structure['A']['total'][key]
                comp_val = structure['C']['total'][key]
                diff = comparison['difference'][key]
                ratio = comparison['ratio'][key] if comparison['ratio'][key] else 0

                comp_table_data.append([
                    label,
                    f"{base_val:,.0f}",
                    f"{comp_val:,.0f}",
                    f"{diff:,.0f}",
                    f"{ratio:.1f}%"
                ])

            comp_table = Table(comp_table_data, colWidths=[3.5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            elements.append(comp_table)

    # Build PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    pdf_output.seek(0)
    return pdf_output
