# migrate_json_to_mongo.py
import json
from bson import ObjectId
from db import books_col, users_col, borrow_col

with open('library_data.json', 'r') as f:
    data = json.load(f)

# Insert books
for book_id, b in data.get('books', {}).items():
    doc = b.copy()
    # Keep the original book_id as a string field for compatibility with app
    doc['book_id'] = str(book_id)
    # Remove any Mongo-specific _id if present
    doc.pop('_id', None)
    books_col.insert_one(doc)

# Insert users
for user_id, u in data.get('users', {}).items():
    doc = u.copy()
    doc['user_id'] = str(user_id)
    doc.pop('_id', None)
    users_col.insert_one(doc)

# Insert borrow_records
for r in data.get('borrow_records', []):
    rec = r.copy()
    # Ensure user_id and book_id are strings to match above
    rec['user_id'] = str(rec.get('user_id'))
    rec['book_id'] = str(rec.get('book_id'))
    rec.pop('_id', None)
    borrow_col.insert_one(rec)

print("Migration complete")