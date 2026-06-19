import io
import csv
import os
from datetime import datetime
from flask import Blueprint, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import Booking, Room, User
from app.utils import admin_required, log_action

# ReportLab libraries
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

reports_bp = Blueprint('reports', __name__)

FONT_NAME = 'Helvetica'

def register_cyrillic_font():
    """
    Search for Cyrillic TTF fonts in common system paths for Windows and Linux,
    registering the first match so Russian text renders properly in the PDF.
    """
    global FONT_NAME
    paths = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('CyrillicArial', path))
                FONT_NAME = 'CyrillicArial'
                return True
            except Exception:
                continue
    return False

# Trigger font registration
register_cyrillic_font()

@reports_bp.route('/csv')
@login_required
@admin_required('can_export_reports')
def export_csv():
    # Fetch all bookings
    bookings = Booking.query.order_by(Booking.start_at.desc()).all()
    
    # Log audit action
    log_action(
        user_id=current_user.id,
        entity_type='report',
        entity_id=None,
        action='export_csv',
        details='Экспортирован отчет по бронированиям в формате CSV'
    )
    
    # Create an in-memory string buffer
    output = io.StringIO()
    # Add BOM to excel supports Cyrillic encoding correctly
    output.write('\ufeff')
    
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        'ID бронирования', 
        'Название встречи', 
        'Переговорная комната', 
        'Организатор (Email)', 
        'Начало', 
        'Окончание', 
        'Статус'
    ])
    
    for b in bookings:
        writer.writerow([
            b.id,
            b.title,
            b.room.name,
            b.organizer.email,
            b.start_at.strftime('%d.%m.%Y %H:%M'),
            b.end_at.strftime('%d.%m.%Y %H:%M'),
            b.status
        ])
        
    output.seek(0)
    
    # Convert string output to bytes for return
    bytes_output = io.BytesIO(output.getvalue().encode('utf-8'))
    
    filename = f"bookings_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@reports_bp.route('/pdf')
@login_required
@admin_required('can_export_reports')
def export_pdf():
    # Fetch bookings for report
    bookings = Booking.query.order_by(Booking.start_at.desc()).all()
    rooms_count = Room.query.count()
    active_bookings_count = Booking.query.filter_by(status='active').count()
    
    # Log audit action
    log_action(
        user_id=current_user.id,
        entity_type='report',
        entity_id=None,
        action='export_pdf',
        details=f'Экспортирован PDF-отчет о загрузке переговорных комнат ({rooms_count} комнат, {active_bookings_count} активных бронирований)'
    )
    
    # Calculate most popular room
    from sqlalchemy import func
    from app.models import db
    busiest_query = db.session.query(
        Room.name, func.count(Booking.id).label('cnt')
    ).join(Booking).filter(Booking.status.in_(['active', 'completed'])).group_by(Room.name).order_by(db.desc('cnt')).first()
    
    busiest_room_name = busiest_query[0] if busiest_query else "Нет данных"
    
    # Set up in-memory PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=30, 
        leftMargin=30, 
        topMargin=30, 
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    # Setup custom styles with local fonts
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#115e59'),
        spaceAfter=15
    )
    
    text_style = ParagraphStyle(
        'DocText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=8
    )
    
    bold_style = ParagraphStyle(
        'DocBold',
        parent=text_style,
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=8
    )
    
    table_text_style = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#334155')
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Отчет о загрузке переговорных комнат «Peregovorki»", title_style))
    story.append(Spacer(1, 10))
    
    # Info metadata
    story.append(Paragraph(f"<b>Дата формирования отчета:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", text_style))
    story.append(Paragraph(f"<b>Всего переговорных комнат:</b> {rooms_count}", text_style))
    story.append(Paragraph(f"<b>Активных бронирований:</b> {active_bookings_count}", text_style))
    story.append(Paragraph(f"<b>Самая популярная комната:</b> {busiest_room_name}", text_style))
    story.append(Spacer(1, 20))
    
    # Table of bookings data
    table_data = [[
        Paragraph("<b>ID</b>", table_header_style),
        Paragraph("<b>Событие</b>", table_header_style),
        Paragraph("<b>Переговорная</b>", table_header_style),
        Paragraph("<b>Организатор</b>", table_header_style),
        Paragraph("<b>Начало</b>", table_header_style),
        Paragraph("<b>Окончание</b>", table_header_style),
        Paragraph("<b>Статус</b>", table_header_style)
    ]]
    
    for b in bookings[:50]:  # Limit to top 50 in report for clean document flow
        # Status translation for clarity
        status_ru = 'Активно' if b.status == 'active' else 'Отменено' if b.status == 'cancelled' else 'Завершено'
        table_data.append([
            Paragraph(str(b.id), table_text_style),
            Paragraph(b.title, table_text_style),
            Paragraph(b.room.name, table_text_style),
            Paragraph(b.organizer.email, table_text_style),
            Paragraph(b.start_at.strftime('%d.%m %H:%M'), table_text_style),
            Paragraph(b.end_at.strftime('%d.%m %H:%M'), table_text_style),
            Paragraph(status_ru, table_text_style)
        ])
        
    # Table column widths layout
    col_widths = [25, 90, 85, 120, 75, 75, 55]
    t = Table(table_data, colWidths=col_widths)
    
    # Style grid
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#059669')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    
    story.append(t)
    
    if len(bookings) > 50:
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"* Показаны последние 50 из {len(bookings)} бронирований.", text_style))
        
    doc.build(story)
    
    buffer.seek(0)
    filename = f"bookings_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
