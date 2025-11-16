import json
from datetime import datetime, timedelta

def create_overdue_books():
    # Load the library data
    with open('library_data.json', 'r') as f:
        data = json.load(f)
    
    # Find the first borrow record that's not returned
    for record in data['borrow_records']:
        if not record['returned']:
            # Change the due date to 5 days ago to make it overdue
            original_due_date = record['due_date']
            
            # Create a date 5 days ago
            overdue_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
            record['due_date'] = overdue_date
            
            print(f"✅ Made book overdue: Due date changed from {original_due_date} to {overdue_date}")
            
            # Save the modified data
            with open('library_data.json', 'w') as f:
                json.dump(data, f, indent=4)
            
            print("📚 Overdue book created successfully!")
            return
    
    print("❌ No active borrow records found. Please borrow a book first.")
    print("💡 Go to http://127.0.0.1:5000/borrow and borrow a book, then run this script again.")

if __name__ == "__main__":
    create_overdue_books()