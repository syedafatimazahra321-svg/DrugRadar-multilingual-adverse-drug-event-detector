import sqlite3

conn = sqlite3.connect('../data/drugradar.db')

print('Predictions:', conn.execute(
    'SELECT COUNT(*) FROM predictions'
).fetchone()[0])

print('Drugs:', conn.execute(
    'SELECT COUNT(*) FROM drugs'
).fetchone()[0])

conn.close()