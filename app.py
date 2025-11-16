from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from library import Library
import json
from datetime import datetime
from email_service import EmailService

from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
# Secret key for sessions (should be set in .env for production)
app.secret_key = os.getenv('FLASK_SECRET', 'dev-secret')

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

library = Library()

# Landing page: choose role
@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/librarian')
def librarian_portal():
    # Show original public dashboard
    stats = {
        'total_books': len(library.get_all_books()),
        'total_users': len(library.get_all_users()),
        'overdue_books': len(library.get_overdue_books())
    }
    return render_template('index.html', stats=stats)

@app.route('/student')
def student_portal():
    return redirect(url_for('home'))


@login_manager.user_loader
def load_user(user_id):
    return library.get_user(user_id)

@app.route('/')
def index():
    # If a student is already logged in, send them to their dashboard
    if current_user.is_authenticated and current_user.role in ['user', 'student']:
        return redirect(url_for('student_dashboard'))

    # Show role-selection landing page as the site root
    return render_template('landing.html')

@app.route('/books')
def books():
    search_query = request.args.get('search', '')
    if search_query:
        books_list = library.search_books(search_query)
    else:
        books_list = library.get_all_books()
    return render_template('books.html', books=books_list, search_query=search_query)

@app.context_processor
def inject_library():
    return dict(library=library, current_user=current_user)


@app.route('/home')
def home():
    """Landing page with role selection"""
    return render_template('home.html')


def require_role(role):
    """Decorator to require a specific role"""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role and current_user.role != 'admin':
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Redirect to student login"""
    return redirect(url_for('login_student'))


@app.route('/login/student', methods=['GET', 'POST'])
def login_student():
    """Student login page"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = library.get_user_by_email(email)
        if user and user.check_password(password) and user.role in ['user', 'student']:
            login_user(user)
            flash('Logged in as Student', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login_student.html')


@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    """Student self-registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif not name or not email or not password:
            flash('All fields are required', 'danger')
        else:
            existing_user = library.get_user_by_email(email)
            if existing_user:
                flash('Email already registered', 'danger')
            else:
                library.add_user_with_password(name, email, phone, password, role='student')
                flash('Registration successful! Please login', 'success')
                return redirect(url_for('login_student'))
    
    return render_template('register_student.html')


@app.route('/dashboard/librarian')
def librarian_dashboard():
    """Redirect to index (librarian pages are public)"""
    return redirect(url_for('index'))


@app.route('/dashboard/student')
@login_required
def student_dashboard():
    """Student dashboard"""
    if current_user.role not in ['user', 'student']:
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('index'))
    
    borrowed_books = library.get_user_borrowed_books(current_user.user_id)
    total_fine = library.get_user_fines(current_user.user_id)
    available_books = [book for book in library.get_all_books() if book.available > 0]
    
    return render_template('student_dashboard.html', 
                         borrowed_books=borrowed_books,
                         total_fine=total_fine,
                         available_books=available_books)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/books/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        quantity = int(request.form.get('quantity', 1))
        
        if title and author and isbn:
            library.add_book(title, author, isbn, quantity)
            return redirect(url_for('books'))
    
    return render_template('add_book.html')

@app.route('/books/<book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    book = library.get_book(book_id)
    if not book:
        return "Book not found", 404
    
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        quantity = int(request.form.get('quantity', 1))
        
        library.update_book(book_id, title, author, isbn, quantity)
        return redirect(url_for('books'))
    
    return render_template('edit_book.html', book=book)

@app.route('/books/<book_id>/delete', methods=['POST'])
def delete_book(book_id):
    if library.delete_book(book_id):
        return jsonify({'success': True})
    return jsonify({'success': False}), 404

@app.route('/users')
def users():
    users_list = library.get_all_users()
    return render_template('users.html', users=users_list)

@app.route('/users/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if name and email:
            library.add_user(name, email, phone)
            return redirect(url_for('users'))
    
    return render_template('add_user.html')

@app.route('/users/<user_id>')
def user_detail(user_id):
    user = library.get_user(user_id)
    if not user:
        return "User not found", 404
    
    borrowed_books = library.get_user_borrowed_books(user_id)
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('user_detail.html', user=user, borrowed_books=borrowed_books, today=today)

@app.route('/borrow', methods=['GET', 'POST'])
@login_required
def borrow_book():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        book_id = request.form.get('book_id')
        days = int(request.form.get('days', 14))
        
        # For students, enforce borrowing for themselves
        if current_user.role in ['user', 'student'] and user_id != current_user.user_id:
            return jsonify({'success': False, 'message': 'You can only borrow for yourself'}), 403
        
        success, message = library.borrow_book(user_id, book_id, days)
        return jsonify({'success': success, 'message': message})
    
    if current_user.role in ['user', 'student']:
        # Students can only borrow for themselves
        users_list = [current_user]
    else:
        # Librarians can see all users
        users_list = library.get_all_users()
    
    books_list = [book for book in library.get_all_books() if book.available > 0]
    return render_template('borrow.html', users=users_list, books=books_list)

@app.route('/return', methods=['POST'])
def return_book():
    user_id = request.form.get('user_id')
    book_id = request.form.get('book_id')
    
    success, message = library.return_book(user_id, book_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/books')
def api_books():
    books = library.get_all_books()
    return jsonify([book.to_dict() for book in books])

@app.route('/api/users')
def api_users():
    users = library.get_all_users()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/overdue')
def api_overdue():
    overdue = library.get_overdue_books()
    result = []
    for item in overdue:
        result.append({
            'book': item['book'].to_dict(),
            'user': item['user'].to_dict(),
            'borrow_date': item['borrow_date'],
            'due_date': item['due_date']
        })
    return jsonify(result)
  
@app.route('/api/health')
def api_health():
    return jsonify({
        'status': 'healthy',
        'books_count': len(library.get_all_books()),
        'users_count': len(library.get_all_users()),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/stats')
def api_stats():
    total_books = len(library.get_all_books())
    total_users = len(library.get_all_users())
    overdue_books = len(library.get_overdue_books())
    
    # Calculate available books
    available_books = sum(1 for book in library.get_all_books() if book.available > 0)
    
    return jsonify({
        'total_books': total_books,
        'total_users': total_users,
        'overdue_books': overdue_books,
        'available_books': available_books,
        'borrowed_books': total_books - available_books
    })
    
@app.route('/admin/send-notifications', methods=['GET', 'POST'])
def send_notifications():
    """Admin route to manage and send notifications"""
    if request.method == 'POST':
        send_overdue = request.form.get('send_overdue') == 'on'
        send_reminders = request.form.get('send_reminders') == 'on'
        test_mode = request.form.get('test_mode') == 'on'
        
        try:
            if test_mode:
                overdue_count = len([r for r in library.borrow_records 
                                   if not r.returned and r.due_date < datetime.now().strftime('%Y-%m-%d')])
                reminder_count = len([r for r in library.borrow_records 
                                    if not r.returned and 
                                    (datetime.strptime(r.due_date, '%Y-%m-%d').date() - datetime.now().date()).days <= 3])
                
                return jsonify({
                    'success': True,
                    'test_mode': True,
                    'message': 'Test mode: Found notifications to send',
                    'results': {
                        'overdue_notifications': overdue_count if send_overdue else 0,
                        'reminder_notifications': reminder_count if send_reminders else 0
                    }
                })
            else:
                results = library.check_and_send_overdue_notifications(
                    send_overdue=send_overdue,
                    send_reminders=send_reminders
                )
                
                total_notifications = results['overdue_notifications'] + results['reminder_notifications']
                
                if total_notifications > 0:
                    message = f"Successfully sent {total_notifications} notifications"
                else:
                    message = "No notifications were sent based on your selection"
                    
                return jsonify({
                    'success': True,
                    'test_mode': False,
                    'message': message,
                    'results': results
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error sending notifications: {str(e)}',
                'results': {'overdue_notifications': 0, 'reminder_notifications': 0}
            })
    
    overdue_books = library.get_overdue_books()
    reminder_books = []
    
    for record in library.borrow_records:
        if not record.returned:
            try:
                days_until_due = (datetime.strptime(record.due_date, '%Y-%m-%d').date() - datetime.now().date()).days
                if 0 <= days_until_due <= 3:
                    book = library.get_book(record.book_id)
                    user = library.get_user(record.user_id)
                    if book and user:
                        reminder_books.append({
                            'book': book,
                            'user': user,
                            'due_date': record.due_date,
                            'days_until_due': days_until_due
                        })
            except:
                pass
    
    stats = {
        'overdue_count': len(overdue_books),
        'reminder_count': len(reminder_books),
        'total_users': len(library.get_all_users()),
        'total_books': len(library.get_all_books())
    }
    
    return render_template('notifications.html', 
                         stats=stats,
                         overdue_books=overdue_books,
                         reminder_books=reminder_books)

@app.route('/admin/notification-preview')
def notification_preview():
    """Preview what notifications would be sent"""
    overdue_count = len([r for r in library.borrow_records 
                       if not r.returned and r.due_date < datetime.now().strftime('%Y-%m-%d')])
    reminder_count = len([r for r in library.borrow_records 
                        if not r.returned and 
                        (datetime.strptime(r.due_date, '%Y-%m-%d').date() - datetime.now().date()).days <= 3])
    
    return jsonify({
        'overdue_count': overdue_count,
        'reminder_count': reminder_count,
        'total_notifications': overdue_count + reminder_count
    })

@app.route('/users/<user_id>/fines')
def user_fines(user_id):
    """Get user fines"""
    user = library.get_user(user_id)
    if not user:
        return "User not found", 404
    
    total_fine = library.get_user_fines(user_id)
    
    fine_details = []
    for record in library.borrow_records:
        if record.user_id == user_id and record.fine_amount > 0 and not record.fine_paid:
            book = library.get_book(record.book_id)
            if book:
                fine_details.append({
                    'book_title': book.title,
                    'fine_amount': record.fine_amount,
                    'due_date': record.due_date,
                    'returned': record.returned
                })
    
    return render_template('user_fines.html', 
                         user=user, 
                         total_fine=total_fine, 
                         fine_details=fine_details)

@app.route('/users/<user_id>/pay-fine/<book_id>', methods=['POST'])
def pay_fine(user_id, book_id):
    """Mark fine as paid"""
    if library.pay_fine(user_id, book_id):
        return jsonify({'success': True, 'message': 'Fine paid successfully'})
    return jsonify({'success': False, 'message': 'Failed to pay fine'}), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)