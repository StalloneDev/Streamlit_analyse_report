import io
import pandas as pd
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

def export_data_to_excel(data_sheets, current_page=None):
    """
    Export data to Excel file
    
    Args:
        data_sheets: Dictionary of dataframes from the loaded Excel file
        current_page: If specified, export only data for this page. Otherwise export all.
    
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
        
        # Determine which sheets to export
        if current_page:
            sheets_to_export = get_sheets_for_page(current_page)
        else:
            sheets_to_export = data_sheets.keys()
        
        # Export each sheet
        for sheet_name in sheets_to_export:
            if sheet_name in data_sheets:
                df = data_sheets[sheet_name]
                
                # Clean sheet name for Excel compatibility
                clean_name = sheet_name[:31]  # Excel limit
                
                df.to_excel(writer, sheet_name=clean_name, index=False)
                
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
            # Clean and format text (remove markdown, keep basic formatting)
            text = section['text']
            text = text.replace('**', '<b>').replace('**', '</b>')
            text = text.replace('###', '').replace('##', '')
            text = text.replace('- ', '• ')
            text = text.replace('\n\n', '<br/><br/>')
            text = text.replace('\n', '<br/>')
            
            # Split into paragraphs
            paragraphs = text.split('<br/><br/>')
            for para in paragraphs:
                if para.strip():
                    elements.append(Paragraph(para.strip(), text_style))
                    elements.append(Spacer(1, 0.1*inch))
        
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

