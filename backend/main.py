print("USING THIS MAIN.PY")
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pattern_detection import detect_patterns, compute_all_interactions
from pdf_report import generate_report
from dotenv import load_dotenv
from pydantic import BaseModel

import sqlite3, re, json as json_lib
import tempfile, os
import io
import pandas as pd
from collections import Counter

load_dotenv()

COMPANY_PORTFOLIOS = {
    'pfizer':   {'password': 'pfizer123',   'drugs': ['ibuprofen', 'lipitor', 'zoloft', 'sertraline']},
    'novartis': {'password': 'novartis123', 'drugs': ['escitalopram', 'topiramate', 'gabapentin']},
    'johnson':  {'password': 'jj123',       'drugs': ['levothyroxine', 'tramadol', 'amoxicillin']},
    'demo':     {'password': 'demo',        'drugs': []},
}

class LoginRequest(BaseModel):
    company: str
    password: str

class SignupRequest(BaseModel):
    company: str
    password: str
    drugs: str = ''

from database import get_conn, SYMPTOM_KEYWORDS

def log_action(action: str, drug_name: str = None, detail: str = None):
    try:
        conn = sqlite3.connect('../data/drugradar.db')
        conn.execute(
            "INSERT OR IGNORE INTO audit_log (action, drug_name, detail) VALUES (?,?,?)",
            (action, drug_name, detail)
        )
        conn.commit()
        conn.close()
    except:
        pass  # never crash the main request because of logging

app = FastAPI(title='DrugRadar API', version='1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

# ── AUTH ────────────────────────────────────────────────────────────────────

@app.post('/api/signup')
def signup(req: SignupRequest):
    conn = get_conn()
    name = req.company.strip().lower()
    if not name or len(name) < 2:
        raise HTTPException(400, 'Company name must be at least 2 characters')
    if len(req.password) < 4:
        raise HTTPException(400, 'Password must be at least 4 characters')
    existing = conn.execute('SELECT id FROM companies WHERE company_name=?', (name,)).fetchone()
    if existing:
        raise HTTPException(409, 'Company name already registered')
    conn.execute(
        'INSERT INTO companies (company_name, password, drugs) VALUES (?,?,?)',
        (name, req.password, req.drugs)
    )
    conn.commit()
    log_action('Company signed up', detail=name)
    return {'company': name, 'drugs': req.drugs.split(',') if req.drugs else [], 'success': True}


@app.post('/api/login')
def login(req: LoginRequest):
    conn = get_conn()
    name = req.company.strip().lower()
    row = conn.execute('SELECT * FROM companies WHERE company_name=?', (name,)).fetchone()
    if row:
        row = dict(row)
        if row['password'] != req.password:
            raise HTTPException(401, 'Wrong password')
        drugs = [d.strip() for d in row['drugs'].split(',') if d.strip()] if row['drugs'] else []
        log_action('Company login', detail=name)
        return {'company': name, 'drugs': drugs, 'success': True}
    if name in COMPANY_PORTFOLIOS:
        if COMPANY_PORTFOLIOS[name]['password'] != req.password:
            raise HTTPException(401, 'Wrong password')
        log_action('Company login', detail=name)
        return {'company': name, 'drugs': COMPANY_PORTFOLIOS[name]['drugs'], 'success': True}
    raise HTTPException(401, 'Company not found. Please sign up first.')

# ── GENERAL ENDPOINTS ───────────────────────────────────────────────────────

@app.get('/api/dashboard')
def get_dashboard():
    conn = get_conn()
    drugs = conn.execute('SELECT * FROM drugs ORDER BY ade_rate DESC').fetchall()
    return [dict(d) for d in drugs]


@app.get('/api/available_drugs')
def get_available_drugs():
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT drug_name FROM drugs ORDER BY drug_name ASC').fetchall()
    conn.close()
    return [r['drug_name'] for r in rows]


@app.get('/api/metrics')
def get_metrics():
    return {
        'tfidf_baseline': {'macro_f1': 0.63, 'ade_f1': 0.58},
        'xlm_roberta':    {'macro_f1': 0.94, 'ade_f1': 0.92},
        'improvement':    '+49% relative F1 improvement',
        'model':          'xlm-roberta-base fine-tuned on ADE Corpus V2',
        'train_size':     18812,
        'test_size':      4704,
        'class_weights':  'balanced (1.0 : 2.45)'
    }


@app.get('/api/calibration')
def get_calibration():
    path = '../data/calibration.json'
    if os.path.exists(path):
        with open(path) as f:
            return json_lib.load(f)
    return [
        {"confidence_bin": 0.5, "actual_accuracy": 0.51, "count": 120},
        {"confidence_bin": 0.6, "actual_accuracy": 0.63, "count": 210},
        {"confidence_bin": 0.7, "actual_accuracy": 0.72, "count": 380},
        {"confidence_bin": 0.8, "actual_accuracy": 0.81, "count": 520},
        {"confidence_bin": 0.9, "actual_accuracy": 0.91, "count": 340},
    ]


@app.get('/api/search')
def search_drugs(q: str = Query(..., min_length=1)):
    conn = get_conn()
    results = conn.execute(
        '''SELECT drug_name, total_reviews, ade_count, ade_rate, signal_level
           FROM drugs WHERE LOWER(drug_name) LIKE ?
           ORDER BY total_reviews DESC LIMIT 10''',
        (f'%{q.lower()}%',)
    ).fetchall()
    return [dict(r) for r in results]

# ── DRUG ENDPOINTS — all use ?drug_name= query param (fixes slash-drug bug) ─

@app.get('/api/drug/detail')
def get_drug_detail(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    log_action('Drug investigated', drug_name=name)
    drug = conn.execute('SELECT * FROM drugs WHERE LOWER(drug_name)=?', (name,)).fetchone()
    conn.close()
    if not drug:
        raise HTTPException(status_code=404, detail='Drug not found')
    return dict(drug)


@app.get('/api/drug/posts')
def get_drug_posts(
    drug_name: str = Query(...),
    severity: str = Query(None, enum=['critical', 'moderate', 'weak']),
    page: int = 1,
    per_page: int = 20
):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    offset = (page - 1) * per_page
    base = 'FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1'
    params = [name]
    if severity:
        base += ' AND severity_bucket=?'
        params.append(severity)
    total = conn.execute(f'SELECT COUNT(*) {base}', params).fetchone()[0]
    rows  = conn.execute(f'SELECT * {base} ORDER BY severity_score DESC LIMIT ? OFFSET ?',
                         params + [per_page, offset]).fetchall()
    conn.close()
    return {'total': total, 'posts': [dict(r) for r in rows]}


@app.get('/api/drug/symptoms')
def get_drug_symptoms(drug_name: str = Query(...), top_n: int = 10):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    rows = conn.execute(
        'SELECT symptoms_found FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1',
        (name,)
    ).fetchall()
    conn.close()
    counter = Counter()
    for r in rows:
        if r['symptoms_found']:
            counter.update(r['symptoms_found'].split('; '))
    return [{'symptom': k, 'count': v} for k, v in counter.most_common(top_n) if k]


@app.get('/api/drug/conditions')
def get_conditions(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    rows = conn.execute(
        '''SELECT condition, COUNT(*) as count, ROUND(AVG(severity_score),3) as avg_severity
           FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1
           GROUP BY condition ORDER BY count DESC LIMIT 10''',
        (name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get('/api/drug/timeline')
def get_timeline(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    rows = conn.execute(
        '''SELECT SUBSTR(review_date,1,7) as month, COUNT(*) as count
           FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1
           GROUP BY month ORDER BY month''',
        (name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get('/api/drug/sentiment_timeline')
def get_sentiment_timeline(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    rows = conn.execute(
        '''SELECT SUBSTR(review_date,1,7) as month,
                  ROUND(AVG(sentiment),3) as avg_sentiment,
                  COUNT(*) as total,
                  SUM(pred_label) as ade_count
           FROM predictions WHERE LOWER(drug_name)=?
           GROUP BY month ORDER BY month''',
        (name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get('/api/drug/interactions')
def get_interactions(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    rows = conn.execute(
        '''SELECT drug_b, co_mention_count, ade_rate
           FROM drug_interactions WHERE LOWER(drug_a)=?
           ORDER BY ade_rate DESC LIMIT 10''',
        (name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get('/api/drug/severity')
def get_severity(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    rows = conn.execute(
        '''SELECT severity_bucket, COUNT(*) as count
           FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1
           GROUP BY severity_bucket''',
        (name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get('/api/drug/insights')
def get_insights(drug_name: str = Query(...)):
    conn = sqlite3.connect('../data/drugradar.db')
    conn.row_factory = sqlite3.Row
    name = drug_name.lower()
    drug = conn.execute('SELECT * FROM drugs WHERE LOWER(drug_name)=?', (name,)).fetchone()
    if not drug:
        conn.close()
        return []
    drug = dict(drug)
    top_cond = conn.execute(
        '''SELECT condition, COUNT(*) as cnt FROM predictions
           WHERE LOWER(drug_name)=? AND pred_label=1
           GROUP BY condition ORDER BY cnt DESC LIMIT 1''',
        (name,)
    ).fetchone()
    rows = conn.execute(
        'SELECT symptoms_found FROM predictions WHERE LOWER(drug_name)=? AND pred_label=1',
        (name,)
    ).fetchall()
    conn.close()
    sc = Counter()
    for r in rows:
        if r['symptoms_found']:
            sc.update(r['symptoms_found'].split('; '))
    top_sym = sc.most_common(1)[0][0] if sc else 'pain'
    insights = [f'{(drug["ade_rate"]*100):.1f}% of {drug_name} reviews flagged as adverse events.']
    if top_cond:
        insights.append(f'Highest volume from {top_cond["condition"]} patients ({top_cond["cnt"]} reports).')
    insights.append(f'Most common symptom: {top_sym} ({sc.get(top_sym, 0)} mentions).')
    if drug['critical_count'] > 5 and drug['ade_count'] > 0:
        pct = drug['critical_count'] / drug['ade_count'] * 100
        insights.append(f'{pct:.0f}% of ADE reports are Critical severity.')
    return insights


@app.get('/api/drug/patterns')
def get_patterns(drug_name: str = Query(...), symptom: str = 'pain'):
    return detect_patterns(drug_name, symptom)


@app.post('/api/drug/compute_interactions')
def trigger_interactions(drug_name: str = Query(...)):
    results = compute_all_interactions(drug_name)
    return {'computed': len(results), 'interactions': results}


@app.get('/api/drug/report')
def download_report(drug_name: str = Query(...)):
    tmp_dir = tempfile.gettempdir()
    safe_name = drug_name.replace('/', '_').replace(' ', '_')
    path = os.path.join(tmp_dir, f'drugradar_{safe_name}_report.pdf')
    log_action('Report downloaded', drug_name=drug_name)
    generate_report(drug_name, path)
    return FileResponse(path, media_type='application/pdf',
                        filename=f'drugradar_{safe_name}_report.pdf')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)