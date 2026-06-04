# backend/pattern_detection.py
import re
from collections import Counter
from database import get_conn

CONTEXT_PATTERNS = {
    'empty_stomach': [r'empty stomach', r'without food', r'no food'],
    'daily_use':     [r'every day', r'daily', r'each day'],
    'long_term':     [r'weeks?', r'months?', r'long.?term', r'for years?'],
    'evening':       [r'at night', r'before bed', r'evening', r'bedtime'],
    'with_food':     [r'with food', r'after eating', r'after meals?'],
    'high_dose':     [r'high dose', r'double', r'extra dose', r'too much'],
}

def detect_patterns(drug_name: str, symptom: str) -> list:
    conn = get_conn()
    rows = conn.execute(
        '''SELECT review_text FROM predictions
           WHERE LOWER(drug_name)=? AND pred_label=1 AND symptoms_found LIKE ?''',
        (drug_name.lower(), f'%{symptom}%')
    ).fetchall()
    if not rows:
        return []
    total = len(rows)
    pattern_counts = Counter()
    for r in rows:
        text_lower = r['review_text'].lower()
        for pattern_name, regexes in CONTEXT_PATTERNS.items():
            for rx in regexes:
                if re.search(rx, text_lower):
                    pattern_counts[pattern_name] += 1
                    break
    desc_map = {
        'empty_stomach': 'mention taking on empty stomach',
        'daily_use':     'involve daily use',
        'long_term':     'involve long-term use',
        'evening':       'involve evening/bedtime dosing',
        'with_food':     'mention taking with food',
        'high_dose':     'mention high or extra dosing',
    }
    results = []
    for pattern, count in pattern_counts.most_common():
        pct = round(count / total * 100, 1)
        if pct >= 10:
            results.append({
                'pattern': pattern,
                'count': count,
                'percentage': pct,
                'description': f'{pct}% of {symptom} reports {desc_map.get(pattern,"")}'
            })
    return results

def compute_all_interactions(drug_name: str):
    conn = get_conn()
    from database import DRUG_KEYWORDS
    rows = conn.execute(
        '''SELECT review_text, pred_label, drugs_found FROM predictions
           WHERE LOWER(drug_name)=? AND pred_label=1 AND drugs_found IS NOT NULL''',
        (drug_name.lower(),)
    ).fetchall()
    co_counts = Counter()
    ade_with_co = Counter()
    for r in rows:
        drugs = [d.strip() for d in r['drugs_found'].split(';') if d.strip()]
        other_drugs = [d for d in drugs if d != drug_name.lower()]
        for od in other_drugs:
            co_counts[od] += 1
            if r['pred_label'] == 1:
                ade_with_co[od] += 1
    results = []
    for drug_b, count in co_counts.most_common(15):
        if count >= 2:
            ade_rate = round(ade_with_co[drug_b] / count, 3)
            results.append({
                'drug_b': drug_b,
                'co_mention_count': count,
                'ade_rate': ade_rate
            })
            conn.execute(
                '''INSERT OR REPLACE INTO drug_interactions
                   (drug_a, drug_b, co_mention_count, ade_rate) VALUES(?,?,?,?)''',
                (drug_name.lower(), drug_b, count, ade_rate)
            )
    conn.commit()
    return results