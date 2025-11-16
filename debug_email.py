import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔍 Email Configuration Debug")
print("=" * 50)

# Check each environment variable
config_vars = {
    'EMAIL_HOST': os.getenv('EMAIL_HOST'),
    'EMAIL_PORT': os.getenv('EMAIL_PORT'),
    'EMAIL_USERNAME': os.getenv('EMAIL_USERNAME'),
    'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
    'EMAIL_FROM': os.getenv('EMAIL_FROM')
}

for key, value in config_vars.items():
    status = "✅ SET" if value else "❌ MISSING"
    # Don't show the actual password for security
    display_value = value if key != 'EMAIL_PASSWORD' else '***' if value else None
    print(f"{key}: {display_value} ({status})")

print("\n📋 Configuration Status:")
if all(config_vars.values()):
    print("✅ All email variables are set!")
else:
    missing = [k for k, v in config_vars.items() if not v]
    print(f"❌ Missing variables: {', '.join(missing)}")

# Test basic email connection
print("\n🔌 Testing Email Connection...")
try:
    import smtplib
    host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    port = int(os.getenv('EMAIL_PORT', 587))
    
    server = smtplib.SMTP(host, port)
    server.starttls()
    print(f"✅ Can connect to {host}:{port}")
    server.quit()
except Exception as e:
    print(f"❌ Connection failed: {e}")