from library import Library
import os
from dotenv import load_dotenv

load_dotenv()

lib = Library()
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
ADMIN_NAME = os.getenv('ADMIN_NAME', 'Admin')

if not ADMIN_EMAIL or not ADMIN_PASSWORD:
    print('Please set ADMIN_EMAIL and ADMIN_PASSWORD in .env before running this script')
else:
    existing = lib.get_user_by_email(ADMIN_EMAIL)
    if existing:
        print('Admin already exists:', existing.user_id)
    else:
        user = lib.add_user_with_password(ADMIN_NAME, ADMIN_EMAIL, '', ADMIN_PASSWORD, role='admin')
        print('Created admin user:', user.user_id, user.email)
