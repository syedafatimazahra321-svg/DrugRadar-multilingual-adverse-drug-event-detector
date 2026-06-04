from database import init_db, load_predictions

init_db()
load_predictions('../data/predictions_25k.csv')

print("Done!")