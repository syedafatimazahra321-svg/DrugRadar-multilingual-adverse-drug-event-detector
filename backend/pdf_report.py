from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import datetime, os, sqlite3
from collections import Counter

# ── Colour palette matching the React UI ────────────────────────────────────
NAVY        = colors.HexColor('#1B2A4A')
BLUE        = colors.HexColor('#2563EB')
TEAL        = colors.HexColor('#0D9488')
RED         = colors.HexColor('#DC2626')
AMBER       = colors.HexColor('#D97706')
GRAY_DARK   = colors.HexColor('#1F2937')
GRAY_MID    = colors.HexColor('#6B7280')
GRAY_LIGHT  = colors.HexColor('#F3F4F6')
GRAY_BORDER = colors.HexColor('#E5E7EB')
WHITE       = colors.white
RED_BG      = colors.HexColor('#FEF2F2')
AMBER_BG    = colors.HexColor('#FFFBEB')
GREEN_BG    = colors.HexColor('#F0FDF4')
GREEN       = colors.HexColor('#15803D')

W = 174 * mm   # usable page width

def _conn(db_path='../data/drugradar.db'):
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    return c

def _style(name, **kw):
    return ParagraphStyle(name, **kw)

# ── helpers ──────────────────────────────────────────────────────────────────
def _signal_color(level):
    level = (level or '').lower()
    if level == 'high':   return RED,   RED_BG
    if level == 'medium': return AMBER, AMBER_BG
    return GREEN, GREEN_BG

def _severity_color(sev):
    sev = (sev or '').lower()
    if sev == 'critical': return RED
    if sev == 'moderate': return AMBER
    return GRAY_MID

def _sev_bg(sev):
    sev = (sev or '').lower()
    if sev == 'critical': return RED_BG
    if sev == 'moderate': return AMBER_BG
    return GRAY_LIGHT

def _pct(n, d):
    return f'{n/d*100:.1f}%' if d else '0%'

# ── main generator ───────────────────────────────────────────────────────────
def generate_report(drug_name: str, output_path: str, db_path: str = '../data/drugradar.db'):
    conn = _conn(db_path)

    # ── fetch data ────────────────────────────────────────────────────────────
    drug_row = conn.execute(
        'SELECT * FROM drugs WHERE LOWER(drug_name)=?', (drug_name.lower(),)
    ).fetchone()
    if not drug_row:
        conn.close()
        raise ValueError(f'Drug not found: {drug_name}')
    drug = dict(drug_row)

    sym_rows = conn.execute(
        'SELECT symptoms_found FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1',
        (drug_name.lower(),)
    ).fetchall()
    sc = Counter()
    for r in sym_rows:
        if r['symptoms_found']:
            sc.update(r['symptoms_found'].split('; '))
    top_syms = [(s, c) for s, c in sc.most_common(6) if s]

    cond_rows = conn.execute(
        '''SELECT condition, COUNT(*) as cnt, ROUND(AVG(severity_score),2) as avg_sev
           FROM predictions
           WHERE LOWER(drug_name)=? AND pred_label=1
             AND condition IS NOT NULL AND condition != 'nan'
           GROUP BY condition ORDER BY cnt DESC LIMIT 6''',
        (drug_name.lower(),)
    ).fetchall()
    conditions = [dict(r) for r in cond_rows]

    posts = conn.execute(
        '''SELECT review_text, severity_bucket, confidence, rating, symptoms_found
           FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1
           ORDER BY severity_score DESC LIMIT 5''',
        (drug_name.lower(),)
    ).fetchall()
    posts = [dict(p) for p in posts]

    sev_rows = conn.execute(
        '''SELECT severity_bucket, COUNT(*) as cnt
           FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1
           GROUP BY severity_bucket''',
        (drug_name.lower(),)
    ).fetchall()
    sev_map = {r['severity_bucket']: r['cnt'] for r in sev_rows}
    conn.close()

    # ── derived values ────────────────────────────────────────────────────────
    total     = drug['total_reviews']
    ade_count = drug['ade_count']
    ade_rate  = drug['ade_rate']
    signal    = drug['signal_level']
    crit      = drug.get('critical_count', sev_map.get('critical', 0))
    sig_color, sig_bg = _signal_color(signal)
    top_sym_name = top_syms[0][0] if top_syms else 'adverse events'

    highest_risk_cond = None
    if conditions:
        highest_risk_cond = max(conditions, key=lambda x: x['avg_sev'])

    # ── doc setup ─────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm
    )
    story = []

    # ── style helpers ─────────────────────────────────────────────────────────
    H1  = _style('H1',  fontName='Helvetica-Bold',  fontSize=18, textColor=NAVY,      spaceAfter=2)
    H2  = _style('H2',  fontName='Helvetica-Bold',  fontSize=12, textColor=NAVY,      spaceBefore=6, spaceAfter=3)
    H3  = _style('H3',  fontName='Helvetica-Bold',  fontSize=10, textColor=GRAY_DARK, spaceBefore=4, spaceAfter=2)
    BOD = _style('BOD', fontName='Helvetica',        fontSize=9,  textColor=GRAY_DARK, leading=14)
    SM  = _style('SM',  fontName='Helvetica',        fontSize=8,  textColor=GRAY_MID)
    SIG = _style('SIG', fontName='Helvetica-Bold',  fontSize=10, textColor=sig_color, alignment=TA_CENTER)
    CEN = _style('CEN', fontName='Helvetica-Bold',  fontSize=22, textColor=WHITE,     alignment=TA_CENTER)
    SUB = _style('SUB', fontName='Helvetica',        fontSize=9,  textColor=colors.HexColor('#93C5FD'), alignment=TA_CENTER)

    def hr(): return HRFlowable(width='100%', thickness=0.5, color=GRAY_BORDER, spaceAfter=4, spaceBefore=4)
    def sp(n=4): return Spacer(1, n*mm)

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 1 — COVER HEADER
    # ════════════════════════════════════════════════════════════════════════════
    header_data = [[
        Paragraph('DrugRadar', CEN),
        Paragraph('PHARMACOVIGILANCE INTELLIGENCE', SUB),
    ]]
    header_tbl = Table([[Paragraph('DrugRadar', CEN)],
                         [Paragraph('PHARMACOVIGILANCE INTELLIGENCE', SUB)],
                         [Paragraph(f'Safety Report: {drug_name.title()}', SUB)]],
                        colWidths=[W])
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), NAVY),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ]))
    story.append(header_tbl)
    story.append(sp(2))

    # generated date + drug name row
    meta = Table([[
        Paragraph(f'<b>{drug_name.title()}</b>', _style('DN', fontName='Helvetica-Bold', fontSize=14, textColor=NAVY)),
        Paragraph(f'Generated: {datetime.date.today()}   |   Data: {total:,} patient reviews',
                  _style('GT', fontName='Helvetica', fontSize=8, textColor=GRAY_MID, alignment=TA_RIGHT))
    ]], colWidths=[W*0.55, W*0.45])
    meta.setStyle(TableStyle([
        ('VALIGN', (0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING', (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
    ]))
    story.append(meta)
    story.append(hr())

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 2 — PLAIN-ENGLISH SUMMARY BOX
    # ════════════════════════════════════════════════════════════════════════════
    summary_sentences = [
        f'{drug_name.title()} shows <b>{signal.upper()} signal</b>.',
        f'<b>{_pct(ade_count, total)}</b> of <b>{total:,}</b> patient reviews report adverse events ({ade_count} flags).',
        f'Most common complaint: <b>{top_sym_name}</b>.',
    ]
    if highest_risk_cond:
        summary_sentences.append(
            f'Highest-risk patient group: <b>{highest_risk_cond["condition"]}</b> (avg severity {highest_risk_cond["avg_sev"]}).'
        )
    summary_text = '  '.join(summary_sentences)

    summary_tbl = Table([[Paragraph(summary_text,
                                    _style('SUM', fontName='Helvetica', fontSize=9.5,
                                           textColor=GRAY_DARK, leading=15))
                          ]], colWidths=[W])
    summary_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX',        (0,0),(-1,-1), 1, BLUE),
        ('TOPPADDING', (0,0),(-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING', (0,0),(-1,-1), 10),
        ('RIGHTPADDING',(0,0),(-1,-1), 10),
        ('ROUNDEDCORNERS',[4]),
    ]))
    story.append(summary_tbl)
    story.append(sp(4))

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 3 — KEY METRICS  (3 big-number boxes)
    # ════════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Key Safety Metrics', H2))

    def metric_cell(label, value, sub, color):
        return [
            Paragraph(value, _style('MV', fontName='Helvetica-Bold', fontSize=22,
                                    textColor=color, alignment=TA_CENTER)),
            Paragraph(label, _style('ML', fontName='Helvetica-Bold', fontSize=8,
                                    textColor=GRAY_MID, alignment=TA_CENTER)),
            Paragraph(sub,   _style('MS', fontName='Helvetica',      fontSize=7,
                                    textColor=GRAY_MID, alignment=TA_CENTER)),
        ]

    metrics_data = [[
        metric_cell('TOTAL REVIEWS',   f'{total:,}',              'patient posts analysed', NAVY),
        metric_cell('ADE FLAGS',        f'{ade_count}',            'adverse events detected', RED),
        metric_cell('ADE RATE',         f'{ade_rate*100:.1f}%',   'of all reviews', RED),
        metric_cell('CRITICAL',         f'{crit}',                 'high-severity flags', RED),
    ]]
    col_w = W / 4
    metrics_tbl = Table(metrics_data, colWidths=[col_w]*4)
    metrics_tbl.setStyle(TableStyle([
        ('BOX',           (0,0),(-1,-1), 0.5, GRAY_BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, GRAY_BORDER),
        ('BACKGROUND',    (0,0),(-1,-1), WHITE),
        ('TOPPADDING',    (0,0),(-1,-1), 8),
        ('BOTTOMPADDING', (0,0),(-1,-1), 8),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(metrics_tbl)
    story.append(sp(2))

    # Signal badge
    sig_tbl = Table([[Paragraph(f'Signal Level: {signal.upper()}', SIG)]],
                     colWidths=[W])
    sig_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,-1), sig_bg),
        ('BOX',        (0,0),(-1,-1), 1, sig_color),
        ('TOPPADDING', (0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    story.append(sig_tbl)
    story.append(sp(5))
    story.append(hr())

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 4 — TOP SYMPTOMS  +  SEVERITY BREAKDOWN  (two-column)
    # ════════════════════════════════════════════════════════════════════════════
    story.append(Paragraph('Adverse Event Profile', H2))

    # left: symptom table
    sym_header = [Paragraph('Symptom', _style('TH', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
                  Paragraph('Reports', _style('THR', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_RIGHT))]
    sym_body   = [[Paragraph(s.title(), _style('TC', fontName='Helvetica', fontSize=8, textColor=GRAY_DARK)),
                   Paragraph(str(c),    _style('TCR', fontName='Helvetica-Bold', fontSize=8, textColor=BLUE, alignment=TA_RIGHT))]
                  for s, c in top_syms]
    sym_tbl = Table([sym_header] + sym_body, colWidths=[58*mm, 18*mm])
    sym_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, GRAY_LIGHT]),
        ('BOX',           (0,0),(-1,-1), 0.5, GRAY_BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, GRAY_BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))

    # right: severity table
    sev_header = [Paragraph('Severity', _style('TH2', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
                  Paragraph('Count',    _style('TH2R', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_RIGHT)),
                  Paragraph('%',        _style('TH2P', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_RIGHT))]
    sev_body = []
    for bucket in ['critical','moderate','weak']:
        cnt = sev_map.get(bucket, 0)
        sev_body.append([
            Paragraph(bucket.upper(), _style('SB', fontName='Helvetica-Bold', fontSize=8,
                                              textColor=_severity_color(bucket))),
            Paragraph(str(cnt),       _style('SBR', fontName='Helvetica-Bold', fontSize=8,
                                              textColor=GRAY_DARK, alignment=TA_RIGHT)),
            Paragraph(_pct(cnt, ade_count), _style('SBP', fontName='Helvetica', fontSize=8,
                                                    textColor=GRAY_MID, alignment=TA_RIGHT)),
        ])
    sev_tbl = Table([sev_header] + sev_body, colWidths=[40*mm, 18*mm, 18*mm])
    sev_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), NAVY),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, GRAY_LIGHT]),
        ('BOX',           (0,0),(-1,-1), 0.5, GRAY_BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, GRAY_BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('RIGHTPADDING',  (0,0),(-1,-1), 6),
    ]))

    two_col = Table([[sym_tbl, sev_tbl]], colWidths=[80*mm, 80*mm])
    two_col.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(1,0),(1,0),8)]))
    story.append(two_col)
    story.append(sp(5))

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 5 — CONDITION BREAKDOWN
    # ════════════════════════════════════════════════════════════════════════════
    if conditions:
        story.append(hr())
        story.append(Paragraph('Which Patient Groups Are Affected?', H2))
        story.append(Paragraph(
            'ADE reports broken down by the medical condition each patient was treating.',
            _style('CAP', fontName='Helvetica-Oblique', fontSize=8, textColor=GRAY_MID, spaceAfter=4)
        ))

        cond_header = [
            Paragraph('Patient Condition',  _style('CH',  fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
            Paragraph('ADE Reports',        _style('CHR', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_RIGHT)),
            Paragraph('Avg Severity',       _style('CHS', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_RIGHT)),
            Paragraph('Risk Level',         _style('CHL', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, alignment=TA_CENTER)),
        ]
        cond_body = []
        for row in conditions:
            sev_val = float(row['avg_sev'] or 0)
            risk_label = 'HIGH' if sev_val > 0.6 else 'MEDIUM' if sev_val > 0.3 else 'LOW'
            risk_color = RED if sev_val > 0.6 else AMBER if sev_val > 0.3 else GREEN
            cond_body.append([
                Paragraph(str(row['condition']).title(),
                          _style('CR', fontName='Helvetica', fontSize=8, textColor=GRAY_DARK)),
                Paragraph(str(row['cnt']),
                          _style('CRN', fontName='Helvetica-Bold', fontSize=8, textColor=BLUE, alignment=TA_RIGHT)),
                Paragraph(f'{sev_val:.2f}',
                          _style('CRS', fontName='Helvetica-Bold', fontSize=8, textColor=risk_color, alignment=TA_RIGHT)),
                Paragraph(risk_label,
                          _style('CRL', fontName='Helvetica-Bold', fontSize=8, textColor=risk_color, alignment=TA_CENTER)),
            ])

        cond_tbl = Table([cond_header] + cond_body, colWidths=[70*mm, 30*mm, 30*mm, 30*mm])
        cond_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0), NAVY),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE, GRAY_LIGHT]),
            ('BOX',           (0,0),(-1,-1), 0.5, GRAY_BORDER),
            ('INNERGRID',     (0,0),(-1,-1), 0.3, GRAY_BORDER),
            ('TOPPADDING',    (0,0),(-1,-1), 5),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5),
            ('LEFTPADDING',   (0,0),(-1,-1), 6),
            ('RIGHTPADDING',  (0,0),(-1,-1), 6),
        ]))
        story.append(cond_tbl)

        if highest_risk_cond:
            sev_val = float(highest_risk_cond['avg_sev'] or 0)
            risk_color = RED if sev_val > 0.6 else AMBER if sev_val > 0.3 else GREEN
            risk_bg    = RED_BG if sev_val > 0.6 else AMBER_BG if sev_val > 0.3 else GREEN_BG
            callout = Table([[Paragraph(
                f'Highest-risk group: <b>{highest_risk_cond["condition"].title()}</b> — '
                f'avg severity {highest_risk_cond["avg_sev"]} | {highest_risk_cond["cnt"]} reports',
                _style('HRG', fontName='Helvetica', fontSize=9, textColor=risk_color)
            )]], colWidths=[W])
            callout.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,-1), risk_bg),
                ('BOX',        (0,0),(-1,-1), 1, risk_color),
                ('TOPPADDING', (0,0),(-1,-1), 6),
                ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                ('LEFTPADDING', (0,0),(-1,-1), 10),
            ]))
            story.append(sp(2))
            story.append(callout)
        story.append(sp(5))

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 6 — FLAGGED PATIENT POSTS (evidence)
    # ════════════════════════════════════════════════════════════════════════════
    story.append(hr())
    story.append(Paragraph('Patient Evidence — Highest Severity Reports', H2))
    story.append(Paragraph(
        'These are real patient reviews that triggered the highest ADE severity scores. '
        'Confidence % shows how certain the NLP model was.',
        _style('CAP2', fontName='Helvetica-Oblique', fontSize=8, textColor=GRAY_MID, spaceAfter=4)
    ))

    for i, p in enumerate(posts, 1):
        sev_bucket = (p.get('severity_bucket') or 'weak').lower()
        conf       = p.get('confidence', 0)
        rating     = p.get('rating', 'N/A')
        text       = str(p.get('review_text', ''))[:280] + '...'
        symptoms   = [s.strip() for s in (p.get('symptoms_found') or '').split(';') if s.strip()]
        sev_c      = _severity_color(sev_bucket)
        sev_b      = _sev_bg(sev_bucket)

        # header row for the post
        post_header = Table([[
            Paragraph(f'Post {i}', _style('PH', fontName='Helvetica-Bold', fontSize=8, textColor=WHITE)),
            Paragraph(sev_bucket.upper(), _style('PS', fontName='Helvetica-Bold', fontSize=8,
                                                  textColor=sev_c, alignment=TA_CENTER)),
            Paragraph(f'Confidence: {conf*100:.0f}%', _style('PC', fontName='Helvetica', fontSize=8,
                                                               textColor=GRAY_MID, alignment=TA_RIGHT)),
            Paragraph(f'Rating: {rating}/10', _style('PR', fontName='Helvetica', fontSize=8,
                                                       textColor=GRAY_MID, alignment=TA_RIGHT)),
        ]], colWidths=[20*mm, 28*mm, 62*mm, 50*mm])
        post_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(0,0), NAVY),
            ('BACKGROUND', (1,0),(1,0), sev_b),
            ('BOX',        (0,0),(-1,-1), 0.5, GRAY_BORDER),
            ('INNERGRID',  (0,0),(-1,-1), 0.3, GRAY_BORDER),
            ('TOPPADDING', (0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING', (0,0),(-1,-1), 6),
        ]))

        # review text
        post_body = Table([[Paragraph(
            f'"{text}"',
            _style('PT', fontName='Helvetica', fontSize=8.5, textColor=GRAY_DARK, leading=13)
        )]], colWidths=[W])
        post_body.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), sev_b),
            ('LEFTPADDING',   (0,0),(-1,-1), 10),
            ('RIGHTPADDING',  (0,0),(-1,-1), 10),
            ('TOPPADDING',    (0,0),(-1,-1), 6),
            ('BOTTOMPADDING', (0,0),(-1,-1), 6),
            ('BOX',           (0,0),(-1,-1), 0.5, GRAY_BORDER),
        ]))

        story.append(post_header)
        story.append(post_body)

        # symptom tags
        if symptoms:
            tag_text = '   '.join(s.upper() for s in symptoms[:5])
            story.append(Table([[Paragraph(tag_text,
                _style('TAG', fontName='Helvetica-Bold', fontSize=7, textColor=RED))]],
                colWidths=[W]))

        story.append(sp(3))

    # ════════════════════════════════════════════════════════════════════════════
    # SECTION 7 — FOOTER
    # ════════════════════════════════════════════════════════════════════════════
    story.append(hr())
    footer_tbl = Table([[
        Paragraph('DrugRadar Pharmacovigilance Platform',
                  _style('FL', fontName='Helvetica', fontSize=7, textColor=GRAY_MID)),
        Paragraph(f'Generated {datetime.date.today()} | XLM-RoBERTa NLP Model | 0.94 macro-F1',
                  _style('FR', fontName='Helvetica', fontSize=7, textColor=GRAY_MID, alignment=TA_RIGHT)),
    ]], colWidths=[W*0.5, W*0.5])
    footer_tbl.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),4)]))
    story.append(footer_tbl)

    doc.build(story)
    print(f'Report saved: {output_path}')
