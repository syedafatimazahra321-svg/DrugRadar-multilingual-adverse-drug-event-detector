# DrugRadar

### Multilingual Adverse Drug Event Detection System

NLP Final Project based on the SMM4H-HeaRD dataset.

---

## About the Project

DrugRadar detects possible adverse drug events (ADEs) from social media posts and patient discussions in multiple languages.

The system analyzes user-written text and identifies whether a post mentions a harmful reaction or side effect related to a medicine or vaccine.

Supported languages:

* English
* German
* French
* Russian

The project also highlights the part of the sentence that caused the prediction, making the output easier to understand.

---

## Project Goal

Many drug side effects are reported online before they are formally documented.

DrugRadar aims to help in:

* early detection of adverse drug reactions
* multilingual health monitoring
* reducing manual review workload
* improving post-market drug surveillance

---

## Main Features

* Multilingual ADE detection
* Evidence span highlighting
* XLM-RoBERTa based classification
* GPT-4o powered data augmentation
* Streamlit dashboard
* Batch CSV prediction support
* Error analysis and evaluation reports

---

## Novelty

The main contribution of this project is the **error-driven augmentation approach**.

Instead of using random data augmentation, the system:

1. trains a baseline model
2. finds posts the model failed on
3. uses GPT-4o to generate similar examples
4. retrains the model on those difficult cases

This helps the model learn from its own mistakes and improve performance on rare ADE examples.

---

## Tech Stack

* Python
* HuggingFace Transformers
* XLM-RoBERTa
* Streamlit
* spaCy
* OpenAI API

---

## Dataset

This project uses data from:

* SMM4H-HeaRD (requested permission . will switch to this when accquired)
* ade-benchmark-corpus (used right now)
* multilingual patient forum posts

---

## Project Structure

```bash
drugradar/
│
├── 01_dataset_setup.py
├── 02_train_xlmroberta.py
├── 03_gpt4o_augmentation.py
├── 04_span_extraction.py
├── 05_dashboard.py
│
├── data/
├── models/
├── outputs/
└── requirements.txt
```

---


