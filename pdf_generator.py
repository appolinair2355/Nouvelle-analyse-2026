from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_predictions_pdf(predictions, filters=None):
    filename = f"/tmp/rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(
        filename, 
        pagesize="A4",
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a5276'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    elements.append(Paragraph("RAPPORT DES PRÉDICTIONS VIP", title_style))
    
    # Sous-titre
    subtitle = f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
    if filters:
        filtres_txt = " | ".join([f"{k}: {v}" for k, v in filters.items() if v])
        subtitle += f"<br/>Filtres: {filtres_txt}"
    
    elements.append(Paragraph(subtitle, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Statistiques
    total = len(predictions)
    gagnes = len([p for p in predictions if 'gagn' in p['statut'].lower()])
    perdus = len([p for p in predictions if 'perd' in p['statut'].lower()])
    attente = total - gagnes - perdus
    
    stats_data = [
        ['Total', 'Gagnés', 'Perdus', 'En attente'],
        [str(total), str(gagnes), str(perdus), str(attente)]
    ]
    stats_table = Table(stats_data, colWidths=[3*cm]*4)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874a6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#eaf2f8')),
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('FONTSIZE', (0,1), (-1,1), 14),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 30))
    
    # Tableau des prédictions
    if predictions:
        table_data = [['N°', 'Numéro', 'Couleur', 'Statut', 'Date']]
        
        for i, p in enumerate(predictions[:1000], 1):  # Limite 1000
            # Couleur du statut
            statut = p['statut']
            if 'gagn' in statut.lower():
                statut_color = 'green'
            elif 'perd' in statut.lower():
                statut_color = 'red'
            else:
                statut_color = 'orange'
            
            date_str = p['date'][:10] if isinstance(p['date'], str) else str(p['date'])[:10]
            
            table_data.append([
                str(i),
                f"#{p['numero']}",
                p['couleur'],
                f"<font color='{statut_color}'>{statut}</font>",
                date_str
            ])
        
        pred_table = Table(table_data, colWidths=[1.5*cm, 2.5*cm, 4*cm, 4*cm, 3*cm])
        pred_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a5276')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#eaf2f8')])
        ]))
        elements.append(pred_table)
    else:
        elements.append(Paragraph("Aucune prédiction trouvée.", styles['Normal']))
    
    doc.build(elements)
    return filename
