# DrugRadar
### Pharmacovigilance Intelligence — Automated Adverse Drug Event Detection

A full-stack pharmacovigilance platform that automatically detects adverse drug events (ADEs) from patient-written reviews using fine-tuned transformer NLP, and presents safety signals through an interactive web dashboard built for pharmaceutical safety teams.

---

## About the Project

DrugRadar ingests real patient reviews from Drugs.com and classifies each one for adverse drug events using a fine-tuned **XLM-RoBERTa** model trained on the ADE Corpus V2. Results are stored in a structured database and surfaced through a React dashboard that gives safety officers instant, readable drug-safety intelligence — without needing to read thousands of posts manually.

The system covers **50 drugs** across **21,861 patient reviews** and achieves **0.94 macro-F1** on ADE classification — a 49% relative improvement over a TF-IDF logistic regression baseline (0.63).

---

## The Problem It Solves

Pharmaceutical companies are legally required to monitor post-market drug safety. Currently this means safety teams manually read thousands of patient reports every week — slow, error-prone, and unable to scale. DrugRadar automates this pipeline end-to-end.

---

## Key Features

- **Plain-English summary card** — auto-generated one-sentence brief per drug: signal level, ADE rate, top complaint, highest-risk patient group
- **Signal level badge** — each drug is classified as LOW / MEDIUM / HIGH safety signal via z-score anomaly detection on ADE rates
- **Top reported symptoms chart** — horizontal bar chart of the most frequently flagged symptoms per drug
- **Severity breakdown** — Critical / Moderate / Weak classification of flagged posts with colour-coded progress bars
- **Condition breakdown table** — which patient groups report the most ADEs and at what average severity
- **Highest risk group highlight** — actionable callout box surfacing the patient group with highest average ADE severity
- **Context patterns** — plain-English NLP insights about *when* symptoms occur (e.g. "62.5% of bleeding reports involve long-term use")
- **Filterable evidence posts** — ALL / CRITICAL / MODERATE filter buttons on actual patient quotes, with per-post confidence score and symptom highlighting
- **Company login system** — companies register and see only their monitored drug portfolio
- **PDF report download** — one-click professional pharmacovigilance report with executive summary and flagged post samples

---

## NLP Techniques Used

- Fine-tuned transformer classification (XLM-RoBERTa-base) on ADE Corpus V2 (23,516 labelled medical texts)
- TF-IDF baseline comparison proving transformer advantage (0.63 → 0.94 macro-F1, +49% relative improvement)
- LIME post-hoc model interpretability
- Regex-based context pattern detection
- Z-score statistical anomaly detection for ADE spikes

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| ML / NLP | XLM-RoBERTa, HuggingFace Transformers, LIME |
| Backend | FastAPI (Python), SQLite |
| Frontend | React, Recharts |
| Data | ADE Corpus V2 (training), Drugs.com reviews via HuggingFace (inference) |
| Reports | PDF generation |

---

## Dataset

| Dataset | Purpose |
|---------|---------|
| **ADE Corpus V2** | Model training — 23,516 labelled clinical texts |
| **Drugs.com reviews (HuggingFace)** | Inference — 21,861 real patient reviews across 50 drugs |

---

## Project Structure

```
drugradar/
│
├── backend/
│   ├── main.py                  
│   ├── database.py              
│   ├── setup_db.py              
│   ├── check_db.py              
│   ├── pattern_detection.py     
│   ├── pdf_report.py            
│   ├── update_sentiment.py      
│   ├── inject_missing_drugs.py  
│   
│
├── frontend/
│   └── src/
│       └── pages/
│           ├── Dashboard.js     
│           ├── DrugDetail.js    
│           ├── Login.js         
│           └── Signup.js        
│
├── notebooks/
│   ├── 00_quickstart.ipynb
│   ├── 01_dataset_setup.ipynb
│   ├── 02_baseline.ipynb
│   ├── 03_xlmroberta_finetune.ipynb
│   ├── 04_inference.ipynb
│   └── 05_lime.ipynb
│
├── data/
   ├── drugradar.db                     
   ├── predictions_25k_sentiment.csv    
   └── sentiment_monthly.csv           

```

---

## Results

| Model | Macro-F1 |
|-------|----------|
| TF-IDF + Logistic Regression (baseline) | 0.63 |
| XLM-RoBERTa (fine-tuned) | **0.94** |
| Relative improvement | **+49%** |
