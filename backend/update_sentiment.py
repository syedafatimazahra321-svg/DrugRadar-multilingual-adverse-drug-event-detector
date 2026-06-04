import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('../data/drugradar.db')

# Add sentiment column if it doesn't already exist
try:
    conn.execute(
        "ALTER TABLE predictions ADD COLUMN sentiment REAL DEFAULT 0.0"
    )
    conn.commit()
    print("Column added")

except:
    print("Column already exists")

# Load CSV with sentiment scores
df = pd.read_csv('../data/predictions_25k_sentiment.csv')

# Update rows
for _, row in df.iterrows():

    conn.execute(
        """
        UPDATE predictions
        SET sentiment = ?
        WHERE review_text = ?
        AND LOWER(drug_name) = ?
        """,
        (
            float(row.get('sentiment', 0.0)),
            str(row.get('review', '')),
            str(row.get('drug_name', '')).lower()
        )
    )

# Save changes
conn.commit()

print("Sentiment scores updated in database")

conn.close()