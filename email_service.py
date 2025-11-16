import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    try:
        load_dotenv()
    except Exception as e:
        # Could be a UnicodeDecodeError when reading a malformed .env file
        print(f"Warning: failed to load .env file: {e}. Continuing without .env.")
except ImportError:
    print("python-dotenv not installed. Using environment variables or defaults.")
    # You can set default values here if needed
    pass

class EmailService:
    def __init__(self):
        # Use environment variables with fallback values
        self.host = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
        self.port = int(os.getenv('EMAIL_PORT', '587'))
        self.username = os.getenv('EMAIL_USERNAME', '')
        self.password = os.getenv('EMAIL_PASSWORD', '')
        self.from_email = os.getenv('EMAIL_FROM', '')
        self.library_name = os.getenv('LIBRARY_NAME', 'Library Management System')
        self.fine_per_day = float(os.getenv('FINE_PER_DAY', '5'))
    
    def send_email(self, to_email, subject, body):
        """Send email to specified address"""
        # Check if email configuration is complete
        if not all([self.host, self.port, self.username, self.password, self.from_email]):
            error_msg = "❌ Email configuration incomplete. Please check your .env file."
            print(error_msg)
            print(f"   Host: {self.host}")
            print(f"   Port: {self.port}")
            print(f"   Username: {self.username}")
            print(f"   From: {self.from_email}")
            print(f"   Password: {'***' if self.password else 'MISSING'}")
            return False
        
        try:
            print(f"📧 Attempting to send email to: {to_email}")
            print(f"   Server: {self.host}:{self.port}")
            print(f"   From: {self.from_email}")
            print(f"   Subject: {subject}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(body, 'html'))
            
            # Create server connection
            print("   🔌 Connecting to SMTP server...")
            server = smtplib.SMTP(self.host, self.port)
            server.ehlo()
            
            print("   🔐 Starting TLS encryption...")
            server.starttls()
            server.ehlo()
            
            print(f"   👤 Logging in as: {self.username}")
            server.login(self.username, self.password)
            
            # Send email
            print("   📤 Sending email...")
            text = msg.as_string()
            server.sendmail(self.from_email, to_email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication Failed: {e}")
            print("   💡 Common solutions:")
            print("   - For Gmail: Use App Password instead of regular password")
            print("   - Enable 2-Factor Authentication")
            print("   - Check username/password")
            return False
            
        except smtplib.SMTPConnectError as e:
            print(f"❌ SMTP Connection Failed: {e}")
            print("   💡 Common solutions:")
            print("   - Check host/port settings")
            print("   - Check internet connection")
            print("   - Check firewall settings")
            return False
            
        except smtplib.SMTPSenderRefused as e:
            print(f"❌ SMTP Sender Refused: {e}")
            print("   💡 Common solutions:")
            print("   - Check FROM email address")
            print("   - Verify sender permissions")
            return False
            
        except smtplib.SMTPRecipientsRefused as e:
            print(f"❌ SMTP Recipient Refused: {e}")
            print("   💡 Common solutions:")
            print("   - Check recipient email address")
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error sending email: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            return False
    
    def calculate_fine(self, due_date):
        """Calculate fine based on due date"""
        try:
            today = datetime.now().date()
            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            if today <= due_date_obj:
                return 0
            
            days_overdue = (today - due_date_obj).days
            fine_amount = days_overdue * self.fine_per_day
            print(f"   💰 Fine calculated: Rs.{fine_amount:.2f} for {days_overdue} days overdue")
            return fine_amount
            
        except Exception as e:
            print(f"❌ Error calculating fine: {e}")
            return 0
    
    def send_overdue_notification(self, user_email, user_name, book_title, due_date, borrow_date):
        """Send overdue book notification"""
        print(f"📨 Preparing overdue notification for {user_name} ({user_email})")
        
        fine_amount = self.calculate_fine(due_date)
        
        subject = f"📚 Overdue Book Notice - {self.library_name}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .fine-alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📚 Overdue Book Notice</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    
                    <p>This is a friendly reminder that the following book is overdue:</p>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h3>"{book_title}"</h3>
                        <p><strong>Borrowed on:</strong> {borrow_date}</p>
                        <p><strong>Due date:</strong> {due_date}</p>
                    </div>
                    
                    <div class="fine-alert">
                        <h4>⚠️ Fine Information</h4>
                        <p><strong>Current Fine:</strong> Rs.{fine_amount:.2f}</p>
                        <p><em>Fine increases by Rs.{self.fine_per_day:.2f} per day until returned</em></p>
                    </div>
                    
                    <p>Please return the book as soon as possible to avoid additional charges.</p>
                    
                    <p>If you have already returned the book, please ignore this message.</p>
                    
                    <p>Best regards,<br>
                    <strong>{self.library_name} Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = self.send_email(user_email, subject, body)
        if success:
            print(f"✅ Overdue notification sent to {user_name}")
        else:
            print(f"❌ Failed to send overdue notification to {user_name}")
        return success
    
    def send_reminder_notification(self, user_email, user_name, book_title, due_date, borrow_date):
        """Send reminder notification before due date"""
        print(f"📨 Preparing reminder notification for {user_name} ({user_email})")
        
        try:
            days_until_due = (datetime.strptime(due_date, '%Y-%m-%d').date() - datetime.now().date()).days
            print(f"   ⏰ Days until due: {days_until_due}")
        except:
            days_until_due = 0
            print("   ⚠️ Could not calculate days until due")
        
        subject = f"📚 Book Return Reminder - {self.library_name}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ffc107; color: black; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .reminder {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📚 Book Return Reminder</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    
                    <p>This is a friendly reminder about your borrowed book:</p>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h3>"{book_title}"</h3>
                        <p><strong>Borrowed on:</strong> {borrow_date}</p>
                        <p><strong>Due date:</strong> {due_date}</p>
                        <p><strong>Days remaining:</strong> {days_until_due} day(s)</p>
                    </div>
                    
                    <div class="reminder">
                        <h4>💡 Friendly Reminder</h4>
                        <p>Please return the book by the due date to avoid late fees of Rs.{self.fine_per_day:.2f} per day.</p>
                    </div>
                    
                    <p>Thank you for using our library services!</p>
                    
                    <p>Best regards,<br>
                    <strong>{self.library_name} Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = self.send_email(user_email, subject, body)
        if success:
            print(f"✅ Reminder notification sent to {user_name}")
        else:
            print(f"❌ Failed to send reminder notification to {user_name}")
        return success
    
    def send_return_confirmation(self, user_email, user_name, book_title, fine_paid=0):
        """Send confirmation when book is returned"""
        print(f"📨 Preparing return confirmation for {user_name} ({user_email})")
        
        subject = f"📚 Book Return Confirmation - {self.library_name}"
        
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f8f9fa; }}
                .confirmation {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; margin: 15px 0; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📚 Book Return Confirmation</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{user_name}</strong>,</p>
                    
                    <div class="confirmation">
                        <h4>✅ Return Successful</h4>
                        <p>We have successfully received your book:</p>
                        <h3>"{book_title}"</h3>
                    </div>
                    
                    {f"<p><strong>Fine Paid:</strong> Rs {fine_paid:.2f}</p>" if fine_paid > 0 else "<p>No fines were charged for this return.</p>"}
                    
                    <p>Thank you for using our library services. We look forward to serving you again!</p>
                    
                    <p>Best regards,<br>
                    <strong>{self.library_name} Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        success = self.send_email(user_email, subject, body)
        if success:
            print(f"✅ Return confirmation sent to {user_name}")
        else:
            print(f"❌ Failed to send return confirmation to {user_name}")
        return success