# pdf_generators.py
import os
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

from config import PDF_FOLDER, FONT_PATH, FONT_PATH_FALLBACK
from utils import reshape_persian_text, format_number


def register_persian_font():
    try:
        if os.path.exists(FONT_PATH):
            pdfmetrics.registerFont(TTFont('PersianFont', FONT_PATH))
        elif os.path.exists(FONT_PATH_FALLBACK):
            pdfmetrics.registerFont(TTFont('PersianFont', FONT_PATH_FALLBACK))
    except:
        pass
    
    try:
        font_paths = [
            "C:/Windows/Fonts/B Nazanin.ttf",
            "C:/Windows/Fonts/Tahoma.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont('PersianFontHistory', path))
                break
    except:
        pass


def generate_statement_pdf(account_code, account_name, data):
    register_persian_font()
    
    filename = f"statement_{account_code}_{int(time.time())}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=25, leftMargin=25, 
                            topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', fontName='PersianFont', fontSize=18, 
                                  leading=22, alignment=TA_CENTER, textColor=colors.HexColor('#1a1a2e'))
    info_style = ParagraphStyle('InfoStyle', fontName='PersianFont', fontSize=11, 
                                 leading=16, alignment=TA_RIGHT, textColor=colors.HexColor('#2c3e50'))
    header_style = ParagraphStyle('HeaderStyle', fontName='PersianFont', fontSize=10, 
                                   leading=14, alignment=TA_RIGHT, textColor=colors.white)
    cell_style = ParagraphStyle('CellStyle', fontName='PersianFont', fontSize=9, 
                                 leading=13, alignment=TA_RIGHT, textColor=colors.HexColor('#2c3e50'))
    date_cell_style = ParagraphStyle('DateCellStyle', fontName='PersianFont', fontSize=8, 
                                      leading=11, alignment=TA_RIGHT, textColor=colors.HexColor('#2c3e50'))
    
    story.append(Paragraph(reshape_persian_text("صورتحساب مشتری"), title_style))
    story.append(Spacer(1, 15))
    
    info_text = f"""
    <b>نام مشتری:</b> {account_name}<br/>
    <b>کد حساب:</b> {account_code}<br/>
    <b>بازه زمانی:</b> {data['from_date']} تا {data['to_date']}
    """
    story.append(Paragraph(reshape_persian_text(info_text), info_style))
    story.append(Spacer(1, 15))
    
    headers = ['مانده (ریال)', 'بستانکار (ریال)', 'بدهکار (ریال)', 'شرح', 'نوع', 'تاریخ', 'شماره', 'ردیف']
    table_data = [[Paragraph(reshape_persian_text(h), header_style) for h in headers]]
    
    for trans in data['transactions']:
        balance_val = trans['balance']
        if balance_val > 0:
            balance_text = f"<font color='#c0392b'>{format_number(balance_val)}</font>"
        elif balance_val < 0:
            balance_text = f"<font color='#27ae60'>{format_number(abs(balance_val))}</font>"
        else:
            balance_text = "0"
        
        row = [
            Paragraph(balance_text, cell_style),
            Paragraph(format_number(trans['cred']) if trans['cred'] > 0 else '0', cell_style),
            Paragraph(format_number(trans['debt']) if trans['debt'] > 0 else '0', cell_style),
            Paragraph(reshape_persian_text(trans['description']), cell_style),
            Paragraph(reshape_persian_text(trans['type']), cell_style),
            Paragraph(reshape_persian_text(trans['date']), date_cell_style),
            Paragraph(str(trans['doc_num']), cell_style),
            Paragraph(str(trans['row']), cell_style)
        ]
        table_data.append(row)
    
    col_widths = [95, 80, 80, 140, 55, 55, 45, 30]
    
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    
    balance = data['final_balance']
    balance_value = format_number(abs(balance))
    if balance > 0:
        status_text = f"{balance_value} (بدهکار)"
        status_color = colors.HexColor('#fff5f5')
        status_text_color = colors.HexColor('#c0392b')
    elif balance < 0:
        status_text = f"{balance_value} (طلبکار)"
        status_color = colors.HexColor('#f0fff4')
        status_text_color = colors.HexColor('#27ae60')
    else:
        status_text = f"{balance_value} (تسویه)"
        status_color = colors.HexColor('#f0f8ff')
        status_text_color = colors.HexColor('#f39c12')

    summary_headers = ['مانده نهایی', 'جمع بستانکار', 'جمع بدهکار']
    summary_style_title = ParagraphStyle('SumTitle', fontName='PersianFont', fontSize=11, 
                                          alignment=TA_RIGHT, textColor=colors.HexColor('#2c3e50'))
    
    summary_data = [
        [Paragraph(reshape_persian_text(h), summary_style_title) for h in summary_headers],
        [
            Paragraph(reshape_persian_text(status_text), 
                     ParagraphStyle('S1', fontName='PersianFont', fontSize=11, alignment=TA_RIGHT, 
                                   textColor=status_text_color)),
            Paragraph(format_number(data['total_cred']), 
                     ParagraphStyle('S2', fontName='PersianFont', fontSize=11, alignment=TA_RIGHT, 
                                   textColor=colors.HexColor('#27ae60'))),
            Paragraph(format_number(data['total_debt']), 
                     ParagraphStyle('S3', fontName='PersianFont', fontSize=11, alignment=TA_RIGHT, 
                                   textColor=colors.HexColor('#c0392b')))
        ]
    ]
    
    sum_table = Table(summary_data, colWidths=[185, 180, 180])
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), status_color),
        ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#f0fff4')),
        ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#fff5f5')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cccccc')),
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    
    story.append(sum_table)
    
    doc.build(story)
    return filepath


def generate_history_pdf(customer_code, customer_name, data):
    register_persian_font()
    
    filename = f"history_{customer_code}_{int(time.time())}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    
    page_width, page_height = landscape(A4)
    margin = 50 
    content_width = page_width - (2 * margin)
    rows_per_page = 18  
    
    current_font = 'PersianFontHistory' if 'PersianFontHistory' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    page_num = 1
    start_idx = 0
    total_rows = len(data['transactions'])
    
    while start_idx < total_rows:
        end_idx = min(start_idx + rows_per_page, total_rows)
        page_rows = data['transactions'][start_idx:end_idx]
        y = page_height - margin
        
        c.setFont(current_font, 16)
        title = reshape_persian_text("سابقه کامل حساب مشتری")
        title_width = c.stringWidth(title, current_font, 16)
        c.drawString((page_width - title_width) / 2, y, title)
        y -= 35
        
        c.setFont(current_font, 11)
        c.drawRightString(page_width - margin, y, reshape_persian_text(f"نام مشتری: {customer_name}"))
        c.drawString(margin, y, reshape_persian_text(f"صفحه: {page_num}"))
        y -= 20
        c.drawRightString(page_width - margin, y, reshape_persian_text(f"کد حساب: {customer_code}"))
        c.drawString(margin, y, reshape_persian_text(f"تعداد کل تراکنش‌ها: {total_rows}"))
        y -= 30
        
        table_data = []
        headers = ['ردیف', 'شماره سند', 'تاریخ', 'نوع', 'شرح تراکنش', 'تعداد', 'بدهکار (ریال)', 'بستانکار (ریال)', 'مانده (ریال)']
        table_data.append([reshape_persian_text(h) for h in headers])
        
        for trans in page_rows:
            balance_val = trans['balance']
            if balance_val > 0:
                balance_str = f"{format_number(balance_val)} (بدهکار)"
            elif balance_val < 0:
                balance_str = f"{format_number(abs(balance_val))} (طلبکار)"
            else:
                balance_str = "0"
                
            row = [
                str(trans['row']),
                str(trans['doc_num']),
                trans['date'],
                reshape_persian_text(trans['type_code']),
                reshape_persian_text(trans['description']),
                str(trans['item_count']),
                format_number(trans['debt']) if trans['debt'] > 0 else '',
                format_number(trans['cred']) if trans['cred'] > 0 else '',
                reshape_persian_text(balance_str)
            ]
            table_data.append(row)
            
        col_widths = [30, 50, 65, 45, 210, 45, 90, 90, 110]
        table = Table(table_data, colWidths=col_widths)
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), current_font),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa'))
        table.setStyle(style)
        
        table_width, table_height = table.wrap(content_width, 0)
        table.drawOn(c, (page_width - table_width) / 2, y - table_height)
        y = y - table_height - 35
        
        if end_idx >= total_rows:
            if y < 110: 
                c.showPage()
                y = page_height - margin
                
            box_width = (content_width - 40) // 3
            box_height = 55
            
            c.setFillColor(colors.HexColor('#fff5f5'))
            c.setStrokeColor(colors.HexColor('#c0392b'))
            c.rect(page_width - margin - box_width, y - box_height, box_width, box_height, fill=True, stroke=True)
            c.setFillColor(colors.black)
            c.setFont(current_font, 11)
            c.drawCentredString(page_width - margin - box_width/2, y - box_height + 32, reshape_persian_text("جمع بدهکار"))
            c.drawCentredString(page_width - margin - box_width/2, y - box_height + 12, format_number(data['total_debt']))
            
            c.setFillColor(colors.HexColor('#f0fff4'))
            c.setStrokeColor(colors.HexColor('#27ae60'))
            c.rect(page_width - margin - 2*box_width - 20, y - box_height, box_width, box_height, fill=True, stroke=True)
            c.setFillColor(colors.black)
            c.setFont(current_font, 11)
            c.drawCentredString(page_width - margin - 1.5*box_width - 20, y - box_height + 32, reshape_persian_text("جمع بستانکار"))
            c.drawCentredString(page_width - margin - 1.5*box_width - 20, y - box_height + 12, format_number(data['total_cred']))
            
            c.setFillColor(colors.HexColor('#f0f8ff'))
            c.setStrokeColor(colors.HexColor('#2980b9'))
            c.rect(margin, y - box_height, box_width, box_height, fill=True, stroke=True)
            c.setFillColor(colors.black)
            c.setFont(current_font, 11)
            c.drawCentredString(margin + box_width/2, y - box_height + 32, reshape_persian_text("مانده نهایی"))
            final_balance = data['final_balance']
            balance_text = f"{format_number(abs(final_balance))} (بدهکار)" if final_balance > 0 else (f"{format_number(abs(final_balance))} (طلبکار)" if final_balance < 0 else "0 (تسویه)")
            c.drawCentredString(margin + box_width/2, y - box_height + 12, reshape_persian_text(balance_text))
            
        if end_idx < total_rows:
            c.showPage()
            page_num += 1
        start_idx = end_idx
        
    c.save()
    return filepath
