import io
import pandas as pd
try:
    import plotly.io as pio
    # Test if kaleido is working
    pio.kaleido.scope.chromium_args += ("--single-process",)
except Exception as e:
    print(f"Warning: Plotly image export may not work: {e}")
    import plotly.io as pio
from datetime import datetime
import xlsxwriter
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import base64
import re

def export_data_to_excel(data_sheets, current_page=None, report_content=None):
    """
    Export data to Excel file with optional report content (charts, text)
    
    Args:
        data_sheets: Dictionary of dataframes from the loaded Excel file
        current_page: If specified, export only data for this page. Otherwise export all.
        report_content: List of dictionaries with 'title', 'figure', 'text', etc. (from pdf_generators)
    
    Returns:
        BytesIO object containing the Excel file
    """
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Format for headers
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Format for text wrapping
        text_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
        title_format = workbook.add_format({'bold': True, 'font_size': 14})
        
        if report_content:
            # Check if it's a structured report (dict of sheets) or flat list
            if isinstance(report_content, dict):
                # Structured export - Multiple sheets
                for sheet_title, section_content in report_content.items():
                    worksheet = workbook.add_worksheet(sheet_title[:31]) # Excel limit
                    worksheet.set_column('A:A', 50) 
                    worksheet.set_column('B:G', 12)
                    
                    row = 0
                    worksheet.write(row, 0, sheet_title, title_format)
                    row += 2
                    
                    # Write content for this section (same logic as before)
                    for section in section_content:
                         # Title
                        if 'title' in section and section['title']:
                            worksheet.write(row, 0, section['title'], title_format)
                            row += 1
                        
                        # Metrics (text representation)
                        if 'metrics' in section and section['metrics']:
                            for m in section['metrics']:
                                metric_text = f"{m.get('label')}: {m.get('value')}"
                                worksheet.write(row, 0, metric_text)
                                row += 1
                            row += 1

                        # Text interpretation
                        if 'text' in section and section['text']:
                            text = section['text'].strip()
                            # Clean up markdown for Excel
                            text = text.replace('**', '').replace('###', '').replace('##', '')
                            text = text.replace('- ', '• ')
                            worksheet.write(row, 0, text, text_format)
                            # Estimate height based on newlines and wrapped text
                            lines = text.count('\n') + (len(text) // 60)
                            row += max(1, lines) + 1
                        
                        # Chart
                        if 'figure' in section and section['figure'] is not None:
                            try:
                                img_bytes = pio.to_image(section['figure'], format='png', width=800, height=450, scale=1)
                                image_data = io.BytesIO(img_bytes)
                                worksheet.insert_image(row, 1, 'chart.png', {'image_data': image_data, 'x_scale': 0.7, 'y_scale': 0.7})
                                row += 15 
                            except Exception:
                                worksheet.write(row, 1, "[Graphique non disponible]")
                                row += 1
                        
                        # Table
                        if 'table' in section and section['table'] is not None:
                            df = section['table'].head(50)
                            for col_num, value in enumerate(df.columns.values):
                                worksheet.write(row, col_num, value, header_format)
                            for i, record in enumerate(df.values):
                                for j, val in enumerate(record):
                                    val_str = str(val) if pd.notna(val) else ""
                                    worksheet.write(row + 1 + i, j, val_str)
                            row += len(df) + 2
                        
                        row += 1

            else:
                # Legacy behavior - specific report for one page or full report (list)
                # If list, put all in one "Rapport Analyse" sheet
                worksheet = workbook.add_worksheet("Rapport Analyse")
                # ... (rest of legacy code is fine, checking data loop below)

        # Determine which sheets to export (Data sheets)
        if current_page:
            sheets_to_export = get_sheets_for_page(current_page)
        else:
            sheets_to_export = data_sheets.keys()
        
        # Track created sheets to avoid duplicates
        existing_sheets = set(writer.book.sheetnames.keys())

        # Export each sheet (Data)
        for sheet_name in sheets_to_export:
            if sheet_name in data_sheets:
                df = data_sheets[sheet_name]
                
                # Clean sheet name for Excel compatibility
                clean_name = sheet_name[:31]  # Excel limit
                
                # Should not collide with report sheets (which occupy "Notifications", etc.)
                # If collision, append " (Data)"
                if clean_name.lower() in [s.lower() for s in existing_sheets]:
                    clean_name = f"{clean_name[:24]} (Data)"
                
                df.to_excel(writer, sheet_name=clean_name, index=False)
                existing_sheets.add(clean_name)
                
                # Get worksheet object
                worksheet = writer.sheets[clean_name]
                
                # Format headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-adjust column width
                    column_len = max(df[value].astype(str).map(len).max(), len(value))
                    worksheet.set_column(col_num, col_num, min(column_len + 2, 50))
    
    output.seek(0)
    return output


def get_sheets_for_page(page):
    """Map analysis page to corresponding data sheets"""
    page_mapping = {
        'synthese': ['duree_distance', 'trajets_non_autorises', 'conduite_journee', 'conduite_nocturne'],
        'duree': ['duree_distance'],
        'trajets': ['trajets_non_autorises'],
        'jour_nuit': ['conduite_journee', 'conduite_nocturne'],
        'limitation_vitesse': ['conduite_journee', 'conduite_nocturne', 'vitesse'],
        'notifications': ['notifications'],
        'temps_poi': ['temps_poi'],
        'visites_poi': ['visites_poi'],
        'vitesse': ['vitesse']
    }
    return page_mapping.get(page, [])


def export_chart_to_image(fig, format='png'):
    """
    Convert a Plotly figure to image bytes
    
    Args:
        fig: Plotly figure object
        format: Image format ('png', 'jpg', 'svg')
    
    Returns:
        BytesIO object containing the image
    """
    img_bytes = pio.to_image(fig, format=format, width=1200, height=600)
    return io.BytesIO(img_bytes)


def create_html_report(page_name, charts_data, interpretations):
    """
    Create an HTML report that can be saved or printed to PDF
    
    Args:
        page_name: Name of the analysis page
        charts_data: List of tuples (chart_title, fig_object)
        interpretations: List of interpretation text blocks
    
    Returns:
        HTML string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Rapport d'Analyse - {page_name}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
            }}
            .section {{
                background: white;
                padding: 25px;
                margin-bottom: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .section h2 {{
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
                margin-top: 0;
            }}
            .chart {{
                margin: 20px 0;
                text-align: center;
            }}
            .chart img {{
                max-width: 100%;
                border-radius: 5px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            }}
            .interpretation {{
                background: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px 20px;
                margin: 15px 0;
                border-radius: 5px;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
            }}
            @media print {{
                body {{ margin: 20px; }}
                .section {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Rapport d'Analyse - {page_name}</h1>
            <p>BP - SADCI GAS PARAKOU</p>
            <p>Généré le {timestamp}</p>
        </div>
    """
    
    # Add charts and interpretations
    for i, (title, interpretation) in enumerate(zip(charts_data, interpretations)):
        html += f"""
        <div class="section">
            <h2>{title}</h2>
        """
        
        if interpretation:
            html += f"""
            <div class="interpretation">
                {interpretation}
            </div>
        """
        
        html += """
        </div>
        """
    
    html += """
        <div class="footer">
            <p>Document généré automatiquement par Data Insights Explorer</p>
        </div>
    </body>
    </html>
    """
    
    return html


def get_filename(page_name, file_format):
    """Generate filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    page_clean = page_name.replace(" ", "_").replace("/", "_")
    return f"Rapport_{page_clean}_{timestamp}.{file_format}"


def create_pdf_report(page_name, charts_and_text):
    """
    Create a PDF report with charts and interpretations
    
    Args:
        page_name: Name of the analysis page
        charts_and_text: List of dictionaries with 'title', 'figure' (plotly fig or None), and 'text' keys
    
    Returns:
        BytesIO object containing the PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=50, leftMargin=50,
                           topMargin=50, bottomMargin=50)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    text_style = ParagraphStyle(
        'CustomText',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=10,
        leading=14
    )
    
    # Style pour les métriques
    metric_style = ParagraphStyle(
        'Metric',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    metric_label_style = ParagraphStyle(
        'MetricLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    
    # Title page
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph(f"📊 Rapport d'Analyse", title_style))
    elements.append(Paragraph(page_name, title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("BP - SADCI GAS PARAKOU", subtitle_style))
    elements.append(Paragraph(f"Généré le {timestamp}", subtitle_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(PageBreak())
    
    # Add content sections
    for section in charts_and_text:
        # Section title
        if 'title' in section and section['title']:
            elements.append(Paragraph(section['title'], heading_style))
            elements.append(Spacer(1, 0.2*inch))
            
        # Metrics
        if 'metrics' in section and section['metrics']:
            # Create a table for metrics (up to 4 per row)
            metrics_data = section['metrics']
            if metrics_data:
                # Prepare data for table
                row_data = []
                for m in metrics_data:
                    val = Paragraph(str(m.get('value', '')), metric_style)
                    lbl = Paragraph(m.get('label', ''), metric_label_style)
                    row_data.append([val, lbl])
                
                # If we have metrics, create a table
                # For simplicity in this version, we'll just stack them or do a simple row
                # Let's do a single row table where each cell has value/label
                
                table_data = [[]]
                for m in metrics_data:
                    val = str(m.get('value', ''))
                    lbl = m.get('label', '')
                    cell_text = f"<b>{val}</b><br/><font size=9 color='#777'>{lbl}</font>"
                    table_data[0].append(Paragraph(cell_text, metric_style))
                
                t = Table(table_data, colWidths=[1.5*inch]*len(table_data[0]))
                t.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e0e0e0')),
                    ('ADDBOX', (0,0), (-1,-1), 1, colors.white), # clear borders
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
                    ('ROUNDEDCORNERS', [5, 5, 5, 5]),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.3*inch))

        # Table
        if 'table' in section and section['table'] is not None:
             try:
                df = section['table']
                # Limit rows to avoid huge PDFs
                if len(df) > 50:
                    df = df.head(50)
                    elements.append(Paragraph("<i>(Affichage des 50 premières lignes uniquement)</i>", text_style))
                
                # Convert DataFrame to list of lists
                data_list = [df.columns.values.tolist()] + df.values.tolist()
                
                # Create Table
                # Calculate approximate widths based on content (naive)
                col_widths = None # Auto
                
                t = Table(data_list)
                
                # Add style
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 10),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('BACKGROUND', (0,1), (-1,-1), colors.white),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e0e0e0')),
                    ('FONTSIZE', (0,1), (-1,-1), 9),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                
                elements.append(t)
                elements.append(Spacer(1, 0.3*inch))
             except Exception as e:
                elements.append(Paragraph(f"<i>Tableau non disponible: {str(e)}</i>", text_style))
        
        # Chart
        if 'figure' in section and section['figure'] is not None:
            try:
                # Convert Plotly figure to image
                img_bytes = pio.to_image(section['figure'], format='png', 
                                        width=1400, height=700, scale=2)
                img_buffer = io.BytesIO(img_bytes)
                
                # Add image to PDF
                img = Image(img_buffer, width=6.5*inch, height=3.25*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.3*inch))
            except Exception as e:
                elements.append(Paragraph(f"<i>Graphique non disponible: {str(e)}</i>", text_style))
        
        # Interpretation text
        if 'text' in section and section['text']:
            text = section['text']
            
            # Handle bold text: **text** -> <b>text</b>
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            
            # Clean other markdown
            text = text.replace('###', '').replace('##', '')
            text = text.replace('- ', '&bull; ')
            text = text.replace('\n\n', '<br/><br/>')
            text = text.replace('\n', '<br/>')
            
            # Split into paragraphs to add space between them
            paragraphs = text.split('<br/><br/>')
            for para in paragraphs:
                if para.strip():
                    try:
                        elements.append(Paragraph(para.strip(), text_style))
                        elements.append(Spacer(1, 0.1*inch))
                    except Exception:
                        # Fallback if ReportLab XML parser fails
                        clean_para = para.strip().replace('<b>', '').replace('</b>', '')
                        elements.append(Paragraph(clean_para, text_style))

        
        elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("Document généré automatiquement par Data Insights Explorer", footer_style))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

