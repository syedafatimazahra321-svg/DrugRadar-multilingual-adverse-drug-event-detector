import sqlite3, re, os
from collections import Counter
import pandas as pd

DB_PATH = '../data/drugradar.db'

DRUG_KEYWORDS = {
    'ibuprofen', 'aspirin', 'paracetamol', 'acetaminophen', 'metformin', 'lisinopril',
    'atorvastatin', 'amoxicillin', 'omeprazole', 'sertraline', 'fluoxetine', 'prednisone',
    'levothyroxine', 'amlodipine', 'metoprolol', 'gabapentin', 'tramadol', 'ciprofloxacin',
    'azithromycin', 'warfarin', 'morphine', 'codeine', 'oxycodone', 'naproxen', 'diazepam',
}

SYMPTOM_KEYWORDS = {
    'pain', 'nausea', 'vomiting', 'headache', 'dizziness', 'rash', 'itching', 'fatigue',
    'swelling', 'diarrhea', 'constipation', 'insomnia', 'anxiety', 'fever', 'cough',
    'cramps', 'bloating', 'heartburn', 'bleeding', 'numbness', 'tingling', 'confusion',
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()

    conn.executescript('''
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_name TEXT NOT NULL,
        condition TEXT,
        review_text TEXT NOT NULL,
        rating INTEGER,
        review_date TEXT,
        useful_count INTEGER DEFAULT 0,
        pred_label INTEGER NOT NULL,
        confidence REAL NOT NULL,
        severity_score REAL DEFAULT 0.0,
        severity_bucket TEXT DEFAULT 'weak',
        drugs_found TEXT,
        symptoms_found TEXT
    );

    CREATE TABLE IF NOT EXISTS drugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_name TEXT UNIQUE NOT NULL,
        total_reviews INTEGER DEFAULT 0,
        ade_count INTEGER DEFAULT 0,
        critical_count INTEGER DEFAULT 0,
        ade_rate REAL DEFAULT 0.0,
        signal_level TEXT DEFAULT 'low'
    );

    CREATE TABLE IF NOT EXISTS drug_interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        drug_a TEXT NOT NULL,
        drug_b TEXT NOT NULL,
        co_mention_count INTEGER DEFAULT 0,
        ade_rate REAL DEFAULT 0.0,
        UNIQUE(drug_a, drug_b)
    );

    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        drugs TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    );
    ''')

    conn.commit()
    conn.close()

    print('Database initialized!')


def extract_spans(text):
    tl = text.lower()

    drugs = [d for d in DRUG_KEYWORDS if d in tl]
    symptoms = [s for s in SYMPTOM_KEYWORDS if s in tl]

    return '; '.join(drugs), '; '.join(symptoms)


def load_predictions(csv_path):
    df = pd.read_csv(csv_path)

    conn = get_conn()

    for _, row in df.iterrows():

        drugs_found, symptoms_found = extract_spans(
            str(row.get('review', ''))
        )

        conn.execute('''
        INSERT OR IGNORE INTO predictions
        (
            drug_name,
            condition,
            review_text,
            rating,
            review_date,
            useful_count,
            pred_label,
            confidence,
            severity_score,
            severity_bucket,
            drugs_found,
            symptoms_found
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            str(row.get('drug_name', '')).lower(),
            str(row.get('condition', '')),
            str(row.get('review', '')),
            int(row.get('rating', 5)) if pd.notna(row.get('rating')) else 5,
            str(row.get('date', '')),
            int(row.get('usefulCount', 0)) if pd.notna(row.get('usefulCount')) else 0,
            int(row.get('pred_label', 0)),
            float(row.get('confidence', 0.5)),
            float(row.get('severity_score', 0.0)),
            str(row.get('severity_bucket', 'weak')),
            drugs_found,
            symptoms_found
        ))

    conn.commit()

    print(f'Loaded {len(df)} rows')

    update_drug_summaries(conn)

    conn.close()


def update_drug_summaries(conn):

    rows = conn.execute('''
    SELECT
        drug_name,
        COUNT(*) as total,
        SUM(pred_label) as ade_cnt,
        SUM(
            CASE
                WHEN severity_bucket='critical'
                THEN 1
                ELSE 0
            END
        ) as crit
    FROM predictions
    GROUP BY drug_name
    ''').fetchall()

    for r in rows:

        ade_rate = (
            r['ade_cnt'] / r['total']
            if r['total'] > 0 else 0
        )

        signal = (
            'high'
            if ade_rate > 0.4
            else 'medium'
            if ade_rate > 0.2
            else 'low'
        )

        conn.execute('''
        INSERT OR REPLACE INTO drugs
        (
            drug_name,
            total_reviews,
            ade_count,
            critical_count,
            ade_rate,
            signal_level
        )
        VALUES (?,?,?,?,?,?)
        ''', (
            r['drug_name'],
            r['total'],
            r['ade_cnt'],
            r['crit'],
            round(ade_rate, 4),
            signal
        ))

    conn.commit()

    print('Drug summaries updated!')