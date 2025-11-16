import json
import os
from datetime import datetime, timedelta
from email_service import EmailService
from werkzeug.security import generate_password_hash, check_password_hash

# Optional MongoDB support: if MONGO_URI is set in environment, use MongoDB collections
from dotenv import load_dotenv
try:
    load_dotenv()
except Exception as e:
    # Could be a UnicodeDecodeError when reading a malformed .env file
    print(f"Warning: failed to load .env file: {e}. Continuing without .env.")

USE_MONGO = bool(os.getenv('MONGO_URI'))
if USE_MONGO:
    try:
        from db import books_col, users_col, borrow_col
    except Exception:
        # Leave imports lazy; migration scripts may create db.py later
        books_col = users_col = borrow_col = None


class Book:
    def __init__(self, book_id, title, author, isbn, quantity=1):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.quantity = quantity
        self.available = quantity
    
    def to_dict(self):
        return {
            'book_id': self.book_id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'quantity': self.quantity,
            'available': self.available
        }
    
    @classmethod
    def from_dict(cls, data):
        book = cls(data['book_id'], data['title'], data['author'], data['isbn'], data['quantity'])
        book.available = data['available']
        return book
    

class User:
    def __init__(self, user_id, name, email, phone):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.phone = phone
        self.borrowed_books = []
        self.password_hash = ''
        self.role = 'user'  # roles: user, librarian, admin
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'borrowed_books': self.borrowed_books,
            'password_hash': self.password_hash,
            'role': self.role
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(data['user_id'], data['name'], data['email'], data['phone'])
        user.borrowed_books = data['borrowed_books']
        user.password_hash = data.get('password_hash', '')
        user.role = data.get('role', 'user')
        return user

    # Flask-Login compatibility helpers
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class BorrowRecord:
    def __init__(self, user_id, book_id, borrow_date, due_date, returned=False, fine_amount=0, fine_paid=False):
        self.user_id = user_id
        self.book_id = book_id
        self.borrow_date = borrow_date
        self.due_date = due_date
        self.returned = returned
        self.fine_amount = fine_amount
        self.fine_paid = fine_paid
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'book_id': self.book_id,
            'borrow_date': self.borrow_date,
            'due_date': self.due_date,
            'returned': self.returned,
            'fine_amount': self.fine_amount,
            'fine_paid': self.fine_paid
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data['user_id'], 
            data['book_id'], 
            data['borrow_date'], 
            data['due_date'], 
            data.get('returned', False),
            data.get('fine_amount', 0),
            data.get('fine_paid', False)
        )


class Library:
    def __init__(self, data_file='library_data.json'):
        self.data_file = data_file
        self.books = {}
        self.users = {}
        self.borrow_records = []
        self.email_service = EmailService()
        self.use_mongo = USE_MONGO
        self.load_data()
    
    def save_data(self):
        # Save to MongoDB if enabled, otherwise to JSON file
        if getattr(self, 'use_mongo', False) and books_col is not None:
            # Upsert books
            for book_id, book in self.books.items():
                books_col.update_one({'book_id': book.book_id}, {'$set': book.to_dict()}, upsert=True)

            # Upsert users
            for user_id, user in self.users.items():
                users_col.update_one({'user_id': user.user_id}, {'$set': user.to_dict()}, upsert=True)

            # Replace borrow records (simple approach)
            borrow_col.delete_many({})
            if self.borrow_records:
                borrow_col.insert_many([r.to_dict() for r in self.borrow_records])
            return

        data = {
            'books': {book_id: book.to_dict() for book_id, book in self.books.items()},
            'users': {user_id: user.to_dict() for user_id, user in self.users.items()},
            'borrow_records': [record.to_dict() for record in self.borrow_records]
        }
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_data(self):
        # If MongoDB is enabled and available, load from collections
        if getattr(self, 'use_mongo', False) and books_col is not None:
            # Load books
            try:
                self.books = {}
                for doc in books_col.find():
                    bdata = {k: v for k, v in doc.items() if k != '_id'}
                    if 'book_id' not in bdata:
                        bdata['book_id'] = str(doc.get('_id'))
                    book = Book.from_dict(bdata)
                    self.books[book.book_id] = book

                # Load users
                self.users = {}
                for doc in users_col.find():
                    udata = {k: v for k, v in doc.items() if k != '_id'}
                    if 'user_id' not in udata:
                        udata['user_id'] = str(doc.get('_id'))
                    user = User.from_dict(udata)
                    self.users[user.user_id] = user

                # Load borrow records
                self.borrow_records = []
                for doc in borrow_col.find():
                    rdata = {k: v for k, v in doc.items() if k != '_id'}
                    # Ensure IDs are strings
                    rdata['user_id'] = str(rdata.get('user_id'))
                    rdata['book_id'] = str(rdata.get('book_id'))
                    self.borrow_records.append(BorrowRecord.from_dict(rdata))
                return
            except Exception:
                # Fall back to JSON file if any Mongo error occurs
                pass

        # Fallback: load from JSON file
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                
                self.books = {book_id: Book.from_dict(book_data) 
                             for book_id, book_data in data.get('books', {}).items()}
                
                self.users = {user_id: User.from_dict(user_data) 
                             for user_id, user_data in data.get('users', {}).items()}
                
                self.borrow_records = [BorrowRecord.from_dict(record_data) 
                                      for record_data in data.get('borrow_records', [])]
    
    def add_book(self, title, author, isbn, quantity=1):
        # Create book and persist immediately
        book_id = str(len(self.books) + 1)
        book = Book(book_id, title, author, isbn, quantity)
        self.books[book_id] = book
        if getattr(self, 'use_mongo', False) and books_col is not None:
            books_col.update_one({'book_id': book.book_id}, {'$set': book.to_dict()}, upsert=True)
        else:
            self.save_data()
        return book
    
    def get_book(self, book_id):
        return self.books.get(book_id)
    
    def get_all_books(self):
        return list(self.books.values())
    
    def search_books(self, query):
        query = query.lower()
        results = []
        for book in self.books.values():
            if (query in book.title.lower() or 
                query in book.author.lower() or 
                query in book.isbn):
                results.append(book)
        return results
    
    def update_book(self, book_id, title=None, author=None, isbn=None, quantity=None):
        book = self.books.get(book_id)
        if book:
            if title:
                book.title = title
            if author:
                book.author = author
            if isbn:
                book.isbn = isbn
            if quantity is not None:
                book.quantity = quantity
                book.available = quantity - len([r for r in self.borrow_records 
                                               if r.book_id == book_id and not r.returned])
            self.save_data()
            return True
        return False
    
    def delete_book(self, book_id):
        if book_id in self.books:
            del self.books[book_id]
            # Remove associated borrow records
            self.borrow_records = [r for r in self.borrow_records if r.book_id != book_id]
            self.save_data()
            return True
        return False
    
    def add_user(self, name, email, phone):
        # Backwards-compatible add_user (no password) — creates a regular user
        user_id = str(len(self.users) + 1)
        user = User(user_id, name, email, phone)
        self.users[user_id] = user
        if getattr(self, 'use_mongo', False) and users_col is not None:
            users_col.update_one({'user_id': user.user_id}, {'$set': user.to_dict()}, upsert=True)
        else:
            self.save_data()
        return user

    def add_user_with_password(self, name, email, phone, password, role='user'):
        user_id = str(len(self.users) + 1)
        user = User(user_id, name, email, phone)
        user.set_password(password)
        user.role = role
        self.users[user_id] = user
        if getattr(self, 'use_mongo', False) and users_col is not None:
            users_col.update_one({'user_id': user.user_id}, {'$set': user.to_dict()}, upsert=True)
        else:
            self.save_data()
        return user

    def get_user_by_email(self, email):
        # Try in-memory
        for u in self.users.values():
            if u.email == email:
                return u
        # If Mongo enabled, query collection
        if getattr(self, 'use_mongo', False) and users_col is not None:
            doc = users_col.find_one({'email': email})
            if doc:
                udata = {k: v for k, v in doc.items() if k != '_id'}
                if 'user_id' not in udata:
                    udata['user_id'] = str(doc.get('_id'))
                user = User.from_dict(udata)
                # store in cache
                self.users[user.user_id] = user
                return user
        return None
    
    def get_user(self, user_id):
        return self.users.get(user_id)
    
    def get_all_users(self):
        return list(self.users.values())
    
    def borrow_book(self, user_id, book_id, days=14):
        # If using MongoDB, perform atomic operations
        if getattr(self, 'use_mongo', False) and books_col is not None:
            # Ensure user exists
            user_doc = users_col.find_one({'user_id': user_id})
            book_doc = books_col.find_one({'book_id': book_id})
            if not user_doc or not book_doc:
                return False, "User or book not found"

            # Check existing active borrow
            existing = borrow_col.find_one({'user_id': user_id, 'book_id': book_id, 'returned': False})
            if existing:
                return False, "User already has this book"

            # Atomically decrement available if > 0
            res = books_col.find_one_and_update(
                {'book_id': book_id, 'available': {'$gt': 0}},
                {'$inc': {'available': -1}},
                return_document=True
            )
            if not res:
                return False, "Book not available"

            borrow_date = datetime.now().strftime('%Y-%m-%d')
            due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

            borrow_doc = {
                'user_id': user_id,
                'book_id': book_id,
                'borrow_date': borrow_date,
                'due_date': due_date,
                'returned': False,
                'fine_amount': 0,
                'fine_paid': False
            }
            borrow_col.insert_one(borrow_doc)
            users_col.update_one({'user_id': user_id}, {'$push': {'borrowed_books': book_id}})

            # Update in-memory cache if loaded
            if book_id in self.books:
                self.books[book_id].available = max(0, self.books[book_id].available - 1)
            if user_id in self.users:
                self.users[user_id].borrowed_books.append(book_id)

            # Also record the borrow in in-memory borrow_records so app UI reflects changes
            try:
                self.borrow_records.append(BorrowRecord.from_dict(borrow_doc))
            except Exception:
                # Fallback: create BorrowRecord manually
                self.borrow_records.append(BorrowRecord(user_id, book_id, borrow_date, due_date))

            return True, "Book borrowed successfully"

        # Fallback to JSON/in-memory behavior
        user = self.users.get(user_id)
        book = self.books.get(book_id)

        if not user or not book:
            return False, "User or book not found"

        if book.available <= 0:
            return False, "Book not available"

        active_borrows = [r for r in self.borrow_records 
                         if r.user_id == user_id and r.book_id == book_id and not r.returned]
        if active_borrows:
            return False, "User already has this book"

        borrow_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        record = BorrowRecord(user_id, book_id, borrow_date, due_date)
        self.borrow_records.append(record)
        book.available -= 1
        user.borrowed_books.append(book_id)

        self.save_data()
        return True, "Book borrowed successfully"
    
    def calculate_fine(self, due_date):
        """Calculate fine for overdue book"""
        today = datetime.now().date()
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
        
        if today <= due_date_obj:
            return 0
        
        days_overdue = (today - due_date_obj).days
        fine_per_day = 5  
        return days_overdue * fine_per_day
    
    def check_and_send_overdue_notifications(self, send_overdue=True, send_reminders=True):
        """Check for overdue books and send notifications with options"""
        today = datetime.now().strftime('%Y-%m-%d')
        overdue_notifications_sent = 0
        reminder_notifications_sent = 0
        
        print(f"🔔 Starting notification process...")
        print(f"   Overdue notifications: {'ENABLED' if send_overdue else 'DISABLED'}")
        print(f"   Reminder notifications: {'ENABLED' if send_reminders else 'DISABLED'}")
        
        for record in self.borrow_records:
            if not record.returned:
                due_date_obj = datetime.strptime(record.due_date, '%Y-%m-%d').date()
                today_obj = datetime.now().date()
                days_until_due = (due_date_obj - today_obj).days
                
                user = self.users.get(record.user_id)
                book = self.books.get(record.book_id)
                
                if user and book:
                    if days_until_due < 0 and send_overdue:
                        record.fine_amount = self.calculate_fine(record.due_date)
                        if self.email_service.send_overdue_notification(
                            user.email, user.name, book.title, 
                            record.due_date, record.borrow_date
                        ):
                            overdue_notifications_sent += 1
                    
                    elif 0 <= days_until_due <= 3 and send_reminders:
                        if self.email_service.send_reminder_notification(
                            user.email, user.name, book.title,
                            record.due_date, record.borrow_date
                        ):
                            reminder_notifications_sent += 1
        
        self.save_data()
        
        print(f"📊 Notification results:")
        print(f"   Overdue notifications sent: {overdue_notifications_sent}")
        print(f"   Reminder notifications sent: {reminder_notifications_sent}")
        
        return {
            'overdue_notifications': overdue_notifications_sent,
            'reminder_notifications': reminder_notifications_sent
        }
    
    def return_book(self, user_id, book_id):
        # Mongo-backed return (atomic-ish)
        if getattr(self, 'use_mongo', False) and books_col is not None:
            user_doc = users_col.find_one({'user_id': user_id})
            book_doc = books_col.find_one({'book_id': book_id})
            if not user_doc or not book_doc:
                return False, "User or book not found"

            record = borrow_col.find_one({'user_id': user_id, 'book_id': book_id, 'returned': False})
            if not record:
                return False, "No active borrow record found"

            # Mark returned and calculate fine
            fine_amount = self.calculate_fine(record.get('due_date'))
            borrow_col.update_one({'_id': record['_id']}, {'$set': {'returned': True, 'fine_amount': fine_amount, 'fine_paid': fine_amount == 0}})

            books_col.update_one({'book_id': book_id}, {'$inc': {'available': 1}})
            users_col.update_one({'user_id': user_id}, {'$pull': {'borrowed_books': book_id}})

            # Update in-memory cache if loaded
            if book_id in self.books:
                self.books[book_id].available = min(self.books[book_id].quantity, self.books[book_id].available + 1)
            if user_id in self.users and book_id in self.users[user_id].borrowed_books:
                try:
                    self.users[user_id].borrowed_books.remove(book_id)
                except ValueError:
                    pass

            # Send email
            if fine_amount > 0:
                self.email_service.send_return_confirmation(user_doc.get('email', ''), user_doc.get('name', ''), book_doc.get('title', ''), fine_amount)
            else:
                self.email_service.send_return_confirmation(user_doc.get('email', ''), user_doc.get('name', ''), book_doc.get('title', ''))

            return True, f"Book returned successfully. Fine: Rs {fine_amount:.2f}" if fine_amount > 0 else "Book returned successfully"

        # Fallback: in-memory/json
        user = self.users.get(user_id)
        book = self.books.get(book_id)

        if not user or not book:
            return False, "User or book not found"

        for record in self.borrow_records:
            if (record.user_id == user_id and 
                record.book_id == book_id and 
                not record.returned):
                
                record.returned = True
                book.available += 1
                
                fine_amount = self.calculate_fine(record.due_date)
                record.fine_amount = fine_amount
                
                if book_id in user.borrowed_books:
                    user.borrowed_books.remove(book_id)
                
                if fine_amount > 0:
                    record.fine_paid = True
                    self.email_service.send_return_confirmation(
                        user.email, user.name, book.title, fine_amount
                    )
                else:
                    self.email_service.send_return_confirmation(
                        user.email, user.name, book.title
                    )
                
                self.save_data()
                return True, f"Book returned successfully. Fine: Rs {fine_amount:.2f}" if fine_amount > 0 else "Book returned successfully"

        return False, "No active borrow record found"
    
    def get_user_borrowed_books(self, user_id):
        user_records = [r for r in self.borrow_records if r.user_id == user_id and not r.returned]
        borrowed_books = []
        for record in user_records:
            book = self.books.get(record.book_id)
            if book:
                borrowed_books.append({
                    'book': book,
                    'borrow_date': record.borrow_date,
                    'due_date': record.due_date
                })
        return borrowed_books
    
    def get_overdue_books(self):
        today = datetime.now().strftime('%Y-%m-%d')
        overdue = []
        for record in self.borrow_records:
            if not record.returned and record.due_date < today:
                book = self.books.get(record.book_id)
                user = self.users.get(record.user_id)
                if book and user:
                    overdue.append({
                        'book': book,
                        'user': user,
                        'borrow_date': record.borrow_date,
                        'due_date': record.due_date
                    })
        return overdue

    def get_user_fines(self, user_id):
        """Get total fines for a user"""
        total_fine = 0
        for record in self.borrow_records:
            if record.user_id == user_id and not record.fine_paid:
                total_fine += record.fine_amount
        return total_fine
    
    def pay_fine(self, user_id, book_id):
        """Mark fine as paid for a specific book"""
        for record in self.borrow_records:
            if (record.user_id == user_id and 
                record.book_id == book_id and 
                record.fine_amount > 0 and 
                not record.fine_paid):
                record.fine_paid = True
                self.save_data()
                return True
        return False