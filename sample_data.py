from library import Library

def create_sample_data():
    library = Library()
    
    # Add sample books
    books = [
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "isbn": "9780743273565", "quantity": 3},
        {"title": "To Kill a Mockingbird", "author": "Harper Lee", "isbn": "9780061120084", "quantity": 2},
        {"title": "1984", "author": "George Orwell", "isbn": "9780451524935", "quantity": 4},
        {"title": "Pride and Prejudice", "author": "Jane Austen", "isbn": "9780141439518", "quantity": 3},
        {"title": "The Hobbit", "author": "J.R.R. Tolkien", "isbn": "9780547928227", "quantity": 2},
    ]
    
    for book in books:
        library.add_book(book["title"], book["author"], book["isbn"], book["quantity"])
    
    # Add sample users
    users = [
        {"name": "John Smith", "email": "john.smith@email.com", "phone": "555-0101"},
        {"name": "Emma Johnson", "email": "emma.johnson@email.com", "phone": "555-0102"},
        {"name": "Michael Brown", "email": "michael.brown@email.com", "phone": "555-0103"},
        {"name": "Sarah Davis", "email": "sarah.davis@email.com", "phone": "555-0104"},
    ]
    
    for user in users:
        library.add_user(user["name"], user["email"], user["phone"])
    
    print("Sample data created successfully!")

if __name__ == "__main__":
    create_sample_data()