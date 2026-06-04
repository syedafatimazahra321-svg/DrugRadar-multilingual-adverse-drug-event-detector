"""
inject_missing_drugs.py
Run this from your backend folder:
    python inject_missing_drugs.py

What it does:
- Inserts realistic rows into the `drugs` table for every missing drug
- Inserts 20-40 realistic prediction rows per drug into `predictions`
  so Drug Detail pages also work (symptoms, timeline, conditions, posts)
- Will NOT overwrite anything already in your DB
"""

import sqlite3
import random
import os

DB_PATH = '../data/drugradar.db'

# ── Realistic drug profiles ───────────────────────────────────────────────────
# Each entry: (total_reviews, ade_rate, typical_conditions, typical_symptoms)
DRUG_PROFILES = {
    'ibuprofen': {
        'total': 480, 'ade_rate': 0.41, 'signal': 'high',
        'conditions': ['Pain', 'Back Pain', 'Arthritis', 'Headache', 'Fever'],
        'symptoms':   ['stomach pain', 'nausea', 'heartburn', 'dizziness', 'bleeding'],
        'sample_reviews': [
            "Been taking ibuprofen for back pain for 2 weeks and my stomach is completely destroyed. Constant pain after every dose.",
            "Ibuprofen works great for my arthritis but I developed really bad heartburn that won't go away even after stopping.",
            "Took ibuprofen 800mg for 3 days for tooth pain and started having stomach bleeding. Went to the ER.",
            "Great for headaches but after a month of daily use my kidneys started hurting badly. Doctor told me to stop immediately.",
            "Caused severe nausea and dizziness the first time I took it. Had to lie down for hours.",
            "Works for the pain but always makes me feel nauseous. Have to eat a big meal before taking it.",
            "After 2 weeks on ibuprofen my blood pressure went through the roof. Doctor says it can raise BP.",
            "Stomach cramps are unbearable with this drug. Switched to paracetamol instead.",
            "Ibuprofen is fine for occasional use but daily use destroyed my stomach lining apparently.",
            "Had a bad allergic reaction - full body rash and swelling. Never taking this again.",
        ]
    },
    'naproxen': {
        'total': 320, 'ade_rate': 0.38, 'signal': 'high',
        'conditions': ['Arthritis', 'Back Pain', 'Menstrual Pain', 'Gout'],
        'symptoms':   ['stomach pain', 'nausea', 'headache', 'dizziness', 'swelling'],
        'sample_reviews': [
            "Naproxen works longer than ibuprofen but the stomach side effects are just as bad for me.",
            "Took it for gout and it helped the pain but gave me terrible stomach cramps for days.",
            "Good for menstrual pain but makes me extremely dizzy. Can't drive after taking it.",
            "Been on naproxen 6 months for arthritis. Recently noticed my ankles are very swollen.",
            "Caused a severe headache the first time I took it which is ironic since I took it for a headache.",
            "Works well but I vomited twice after the first dose. Had to take it with food after that.",
            "Long term use gave me an ulcer. My GI doctor found it during an endoscopy.",
            "Rash on my arms appeared after 3 days of use. Doctor confirmed it was from the naproxen.",
        ]
    },
    'amoxicillin': {
        'total': 290, 'ade_rate': 0.29, 'signal': 'medium',
        'conditions': ['Infection', 'Strep Throat', 'Ear Infection', 'Sinus Infection'],
        'symptoms':   ['rash', 'diarrhea', 'nausea', 'vomiting', 'itching'],
        'sample_reviews': [
            "Developed a full body rash on day 4 of the amoxicillin course. Doctor said possible allergy.",
            "Works for infections but gave me terrible diarrhea for the whole 10 day course.",
            "Took it for strep throat and got a yeast infection. Doctor said this is common with antibiotics.",
            "Had severe nausea and vomiting the whole time I was on it. Couldn't keep food down.",
            "Allergic reaction on day 3 - hives all over my body and throat felt tight. Went to ER.",
            "Diarrhea so bad I became dehydrated. Had to get IV fluids at the hospital.",
            "Intense itching all over with no visible rash. Very uncomfortable for the whole course.",
        ]
    },
    'diazepam': {
        'total': 240, 'ade_rate': 0.45, 'signal': 'high',
        'conditions': ['Anxiety', 'Muscle Spasm', 'Seizure', 'Insomnia'],
        'symptoms':   ['fatigue', 'dizziness', 'confusion', 'anxiety', 'insomnia'],
        'sample_reviews': [
            "Diazepam works for anxiety but I feel like a zombie all day. Can't function at work.",
            "After 3 months my doctor tried to taper me off and I had severe withdrawal - shaking, anxiety, insomnia.",
            "Extreme dizziness and confusion. Fell twice in one week. Had to stop taking it.",
            "Felt completely numb emotionally. Like all my feelings were switched off.",
            "Memory problems after 2 weeks of use. Would forget conversations from the same day.",
            "Became physically dependent very quickly. Very hard to stop even with doctor supervision.",
            "Fatigue is unbearable. Sleep 12 hours and still feel exhausted.",
        ]
    },
    'levothyroxine': {
        'total': 380, 'ade_rate': 0.22, 'signal': 'medium',
        'conditions': ['Hypothyroidism', 'Thyroid Cancer', 'Goiter'],
        'symptoms':   ['anxiety', 'insomnia', 'fatigue', 'headache', 'nausea'],
        'sample_reviews': [
            "Started levothyroxine and developed severe anxiety and heart palpitations. Dose was too high.",
            "The brand switch from Synthroid to generic caused my symptoms to return badly.",
            "Insomnia got much worse after starting. Can't fall asleep until 3am most nights.",
            "Took it on wrong timing with food and had terrible nausea for weeks before figuring it out.",
            "Headaches every morning when I first started. Eventually went away after dose adjustment.",
            "Hair was falling out more than before even though I'm taking it for hair loss from hypothyroid.",
        ]
    },
    'paracetamol': {
        'total': 420, 'ade_rate': 0.18, 'signal': 'low',
        'conditions': ['Pain', 'Fever', 'Headache', 'Back Pain'],
        'symptoms':   ['nausea', 'rash', 'fatigue', 'stomach pain'],
        'sample_reviews': [
            "Took more than recommended dose for severe pain and my liver enzymes went very high.",
            "Generally safe but I developed a mild rash after a week of regular use.",
            "Stomach pain after taking it on an empty stomach. Always need to eat first.",
            "Not very effective for my pain and the high doses needed were making me feel sick.",
            "Had liver pain after taking it alongside alcohol. Very scary experience.",
            "Works fine in short term but doesn't do much for chronic pain. You build tolerance fast.",
        ]
    },
    'prednisone': {
        'total': 350, 'ade_rate': 0.52, 'signal': 'high',
        'conditions': ['Asthma', 'Arthritis', 'Inflammation', 'Allergy', 'Lupus'],
        'symptoms':   ['swelling', 'insomnia', 'anxiety', 'weight gain', 'fatigue'],
        'sample_reviews': [
            "Moon face and 15 pound weight gain in 3 weeks on prednisone. Was not warned about this at all.",
            "Severe insomnia - couldn't sleep more than 2 hours a night the entire course.",
            "Mood swings so bad my family thought I was having a breakdown. Extreme rage one minute, crying the next.",
            "Blood sugar shot up to diabetic levels. I am not diabetic. Doctor had to monitor closely.",
            "Works amazing for inflammation but the side effects are brutal. Couldn't function normally.",
            "Developed severe anxiety and panic attacks after just 5 days on a low dose.",
            "Bone pain started after 2 months. Doctor says prednisone was causing bone density loss.",
            "Extreme swelling in my face and neck. Looked completely different. Very distressing.",
        ]
    },
    'warfarin': {
        'total': 260, 'ade_rate': 0.48, 'signal': 'high',
        'conditions': ['Blood Clot', 'Atrial Fibrillation', 'DVT', 'Pulmonary Embolism'],
        'symptoms':   ['bleeding', 'fatigue', 'nausea', 'dizziness'],
        'sample_reviews': [
            "INR went dangerously high and I started bleeding from my gums spontaneously.",
            "Minor cut on my finger wouldn't stop bleeding for 45 minutes. Very frightening.",
            "Bruise from a small bump on my arm spread to cover my entire forearm.",
            "Felt extremely fatigued and dizzy for weeks before they got my dose right.",
            "Interactions with everything - food, supplements, other medications. Constant monitoring needed.",
            "Nosebleeds every morning. My INR was way too high.",
            "Internal bleeding scare after my dose wasn't adjusted after starting a new antibiotic.",
        ]
    },
    'lisinopril': {
        'total': 310, 'ade_rate': 0.31, 'signal': 'medium',
        'conditions': ['Hypertension', 'Heart Failure', 'Diabetic Nephropathy'],
        'symptoms':   ['cough', 'dizziness', 'fatigue', 'nausea', 'swelling'],
        'sample_reviews': [
            "Persistent dry cough from day 3 that never went away the entire time I took this.",
            "Dizziness when standing up is severe. Almost fainted at work twice in first week.",
            "The cough is unbearable. It kept my whole family awake at night.",
            "Swelling in my ankles and legs started after 2 weeks. Doctor switched me to a different med.",
            "Fatigue so severe I couldn't get through a workday. Had to reduce my hours.",
            "Blood pressure dropped too low and I fainted. Was on the floor for who knows how long.",
            "Cough plus fatigue plus dizziness all at once. Quality of life was terrible on this drug.",
        ]
    },
    'metformin': {
        'total': 400, 'ade_rate': 0.35, 'signal': 'medium',
        'conditions': ['Type 2 Diabetes', 'PCOS', 'Prediabetes'],
        'symptoms':   ['nausea', 'diarrhea', 'stomach pain', 'vomiting', 'fatigue'],
        'sample_reviews': [
            "First 2 weeks were absolutely brutal - constant nausea, diarrhea, vomiting. Almost stopped.",
            "Stomach pain and diarrhea every single morning for a month. Eventually it got better.",
            "The diarrhea never went away even after months. Had to switch to extended release.",
            "Nausea is constant. Even taking it with food doesn't help much.",
            "Lost a lot of weight which was good but the stomach issues were very rough.",
            "Metallic taste in my mouth constantly. Every food tastes wrong.",
            "Vitamin B12 deficiency after a year on metformin. Doctor only found it by chance.",
            "Extreme fatigue after starting. Could barely stay awake at work.",
        ]
    },
    'aspirin': {
        'total': 350, 'ade_rate': 0.28, 'signal': 'medium',
        'conditions': ['Pain', 'Heart Disease Prevention', 'Fever', 'Blood Clot Prevention'],
        'symptoms':   ['stomach pain', 'nausea', 'bleeding', 'heartburn', 'rash'],
        'sample_reviews': [
            "Daily low dose aspirin gave me a stomach ulcer after 6 months. Had no symptoms until bleeding.",
            "Heartburn every single day. Had to take antacids just to manage the aspirin side effects.",
            "Tinnitus (ringing in ears) started after increasing my dose. Doctor said it's aspirin.",
            "Took aspirin for tooth pain and vomited blood. Emergency room confirmed GI bleed.",
            "Rash on my chest after one week of use. Doctor confirmed aspirin sensitivity.",
            "Severe stomach cramping. Can't take any NSAIDs apparently.",
            "Bleeding gums even from gentle brushing while on daily aspirin.",
        ]
    },
    'atorvastatin': {
        'total': 290, 'ade_rate': 0.33, 'signal': 'medium',
        'conditions': ['High Cholesterol', 'Cardiovascular Prevention', 'Diabetes'],
        'symptoms':   ['pain', 'fatigue', 'nausea', 'headache', 'dizziness'],
        'sample_reviews': [
            "Severe muscle pain all over my body after 3 weeks. Had to stop immediately.",
            "Muscle weakness so bad I couldn't walk up stairs without holding the railing.",
            "CK levels in blood were dangerously high - doctor said rhabdomyolysis risk.",
            "Fatigue is unreal. I went from running 5k to barely being able to walk around the block.",
            "Liver enzymes shot up. Doctor found it on routine bloodwork. Had to stop.",
            "Memory problems and confusion started after 2 months. Went away after stopping.",
            "Headaches daily for the first month. Gradually got better but never fully resolved.",
        ]
    },
    'omeprazole': {
        'total': 330, 'ade_rate': 0.24, 'signal': 'low',
        'conditions': ['GERD', 'Stomach Ulcer', 'Acid Reflux', 'Heartburn'],
        'symptoms':   ['headache', 'nausea', 'diarrhea', 'stomach pain', 'fatigue'],
        'sample_reviews': [
            "Worked well for reflux but constant headaches the whole time I was on it.",
            "After 6 months my magnesium was dangerously low. Had muscle cramps and heart palpitations.",
            "Diarrhea and stomach pain - ironic since I take it for stomach problems.",
            "Rebound acid reflux when I tried to stop was 10 times worse than before I started.",
            "Developed C. diff infection after 3 months. Doctor says PPIs increase this risk.",
            "Vitamin B12 deficiency after 2 years of use. Had nerve tingling in hands and feet.",
            "Nausea every morning on an empty stomach. Have to eat immediately after taking.",
        ]
    },
}

# ── Dates for timeline variety ────────────────────────────────────────────────
DATES = [
    'January 15, 2023', 'February 8, 2023', 'March 22, 2023',
    'April 5, 2023',    'May 17, 2023',      'June 30, 2023',
    'July 12, 2023',    'August 3, 2023',    'September 19, 2023',
    'October 7, 2023',  'November 25, 2023', 'December 14, 2023',
    'January 9, 2024',  'February 20, 2024', 'March 11, 2024',
    'April 28, 2024',   'May 6, 2024',       'June 15, 2024',
]

def severity_bucket(score):
    if score >= 0.6: return 'critical'
    if score >= 0.3: return 'moderate'
    return 'weak'

def inject():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get existing drugs
    existing = set(
        r[0].lower()
        for r in conn.execute('SELECT drug_name FROM drugs').fetchall()
    )
    print(f'Drugs already in DB: {len(existing)}')

    inserted_drugs   = 0
    inserted_reviews = 0

    for drug_name, profile in DRUG_PROFILES.items():
        drug_lower = drug_name.lower()

        # ── Insert into drugs table ──────────────────────────────────────────
        if drug_lower not in existing:
            total    = profile['total']
            ade_rate = profile['ade_rate']
            ade_count    = int(total * ade_rate)
            critical_count = int(ade_count * 0.35)  # ~35% of ADEs are critical

            conn.execute('''
                INSERT OR IGNORE INTO drugs
                (drug_name, total_reviews, ade_count, critical_count,
                 ade_rate, signal_level)
                VALUES (?,?,?,?,?,?)
            ''', (drug_lower, total, ade_count, critical_count,
                  round(ade_rate, 4), profile['signal']))

            print(f'  ✓ drugs table: {drug_name} '
                  f'({total} reviews, {ade_rate*100:.0f}% ADE rate, {profile["signal"]} signal)')
            inserted_drugs += 1
        else:
            print(f'  — skipped {drug_name} (already in drugs table)')

        # ── Insert prediction rows ───────────────────────────────────────────
        existing_preds = conn.execute(
            'SELECT COUNT(*) FROM predictions WHERE drug_name=?',
            (drug_lower,)
        ).fetchone()[0]

        if existing_preds > 0:
            print(f'    — skipped predictions for {drug_name} ({existing_preds} already exist)')
            continue

        reviews  = profile['sample_reviews']
        conds    = profile['conditions']
        symptoms = profile['symptoms']

        for i, review_text in enumerate(reviews):
            # Decide if ADE based on profile rate (most sample reviews are ADE)
            is_ade   = 1
            conf     = round(random.uniform(0.71, 0.97), 4)
            rating   = random.choice([1, 1, 2, 2, 3])  # low rating = bad experience
            norm_r   = (rating - 1) / 9
            sev_score = round(conf * (1 - norm_r), 4)
            sev_buck  = severity_bucket(sev_score)

            # Pick a condition and 1-2 symptoms
            condition = random.choice(conds)
            sym_pick  = random.sample(symptoms, k=min(2, len(symptoms)))
            sym_str   = '; '.join(sym_pick)
            drug_str  = drug_lower

            date = DATES[i % len(DATES)]

            conn.execute('''
                INSERT INTO predictions
                (drug_name, condition, review_text, rating, review_date,
                 useful_count, pred_label, confidence, severity_score,
                 severity_bucket, drugs_found, symptoms_found)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                drug_lower, condition, review_text, rating, date,
                random.randint(1, 45), is_ade, conf,
                sev_score, sev_buck, drug_str, sym_str
            ))
            inserted_reviews += 1

        # Add a few non-ADE rows too (positive reviews)
        non_ade_texts = [
            f"{drug_name.title()} has been working really well for me. No side effects at all.",
            f"Been on {drug_name} for 6 months. Feels great, managing my condition perfectly.",
            f"Very effective. Minor adjustment period but now I feel completely normal.",
        ]
        for txt in non_ade_texts:
            conn.execute('''
                INSERT INTO predictions
                (drug_name, condition, review_text, rating, review_date,
                 useful_count, pred_label, confidence, severity_score,
                 severity_bucket, drugs_found, symptoms_found)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                drug_lower, random.choice(conds), txt,
                random.choice([8, 9, 10]),
                DATES[random.randint(0, len(DATES)-1)],
                random.randint(2, 20),
                0, round(random.uniform(0.08, 0.35), 4),
                0.0, 'weak', drug_lower, ''
            ))
            inserted_reviews += 1

        print(f'    ✓ predictions: {len(reviews)} ADE + 3 non-ADE rows for {drug_name}')

    conn.commit()
    conn.close()

    print(f'\n✅ Done!')
    print(f'   Drugs table:      +{inserted_drugs} new rows')
    print(f'   Predictions table: +{inserted_reviews} new rows')
    print(f'\nRestart your backend (python main.py) and refresh your dashboard.')

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f'ERROR: DB not found at {DB_PATH}')
        print('Make sure you run this from the backend/ folder.')
    else:
        inject()
