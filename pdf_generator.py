from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_pdf(predictions, filters=None):
    """Génère le PDF des prédictions"""
    filename = f"/tmp/rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize="A4")
    styles = getSampleStyleSheet()
    elements = []
    
    # Titre
    title_style = ParagraphStyle(
        'Title', parent=styles['Heading1'],
        fontSize=18, textColor=colors.HexColor('#1a5276'),
        alignment=TA_CENTER
    )
    elements.append(Paragraph("RAPPORT DES PRÉDICTIONS VIP", title_style))
    elements.append(Spacer(1, 20))
    
    # Stats
    total = len(predictions)
    gagnes = len([p for p in predictions if 'gagn' in p['statut'].lower()])
    perdus = len([p for p in predictions if 'perd' in p['statut'].lower()])
    
    stats = f"Total: {total} | Gagnés: {gagnes} | Perdus: {perdus}"
    elements.append(Paragraph(stats, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Tableau
    if predictions:
        data = [['#', 'Numéro', 'Couleur', 'Statut', 'Date']]
        
        for i, p in enumerate(predictions[:1000], 1):
            date_str = p['date'][:10] if isinstance(p['date'], str) else str(p['date'])[:10]
            
            # Couleur du statut
            statut = p['statut']
            if 'gagn' in statut.lower():
                statut_html = f"<font color='green'>{statut}</font>"
            elif 'perd' in statut.lower():
                statut_html = f"<font color='red'>{statut}</font>"
            else:
                statut_html = f"<font color='orange'>{statut}</font>"
            
            data.append([
                str(i),
                f"#{p['numero']}",
                p['couleur'],
                Paragraph(statut_html, styles['Normal']),
                date_str
            ])
        
        table = Table(data, colWidths=[40, 80, 120, 150, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874a6')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(table)
    
    doc.build(elements)
    return filename
