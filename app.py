import os
from pathlib import Path

# Load .env file (for local testing)
if Path('.env').exists():
    from dotenv import load_dotenv
    load_dotenv()

# Explicit file paths for Render
FIREBASE_CREDS = Path('google-service-account.json')
if not FIREBASE_CREDS.exists():
    with open(FIREBASE_CREDS, 'w') as f:
        f.write(os.getenv('FIREBASE_CREDS_JSON'))  # Will set in Render

# Your existing code...
import json
from dotenv import load_dotenv
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from twilio.rest import Client
from apscheduler.schedulers.blocking import BlockingScheduler
import pytz

# Load .env variables
load_dotenv()

from twilio.rest import Client

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

def invite_to_sandbox(phone_number):
    # Send onboarding link via SMS/email
    invitation = client.messages.create(
        body=f'Click to join class alerts: wa.me/14155238886?text=join%20academy-123',
        from_='+15735153876',  # Your Twilio SMS number
        to=phone_number
    )
    return invitation.sid

def send_daily_notifications():
    """Main function to send daily notifications"""
    try:
        # Google Sheets setup
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            os.getenv("GOOGLE_SHEET_CREDENTIALS"), 
            scope
        )
        client = gspread.authorize(creds)

        # Twilio setup
        twilio_client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        twilio_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

        # Get Sheets
        spreadsheet = client.open_by_key(os.getenv("SPREADSHEET_ID"))
        sheet1 = spreadsheet.worksheet(os.getenv("SHEET1_NAME"))
        sheet2 = spreadsheet.worksheet(os.getenv("SHEET2_NAME"))

        # Read data
        schedule_data = sheet1.get_all_records()
        student_data = sheet2.get_all_records()

        # Today's date in matching format
        today_str = datetime.now(pytz.timezone(os.getenv("TIMEZONE"))).strftime("%-d %b %Y")

        # Create a batch-to-student lookup
        batch_students = {}
        for student in student_data:
            batch = student["Batch"]
            if batch not in batch_students:
                batch_students[batch] = []
            batch_students[batch].append(student)

        # Send personalized messages
        for row in schedule_data:
            if row["Date"].strip() == today_str:
                batch = row["Batch"]
                if batch in batch_students:
                    for student in batch_students[batch]:
                        name = student["Name"]
                        mobile = student["Mobile"]

                        message = f"""
Hi {name} 👋,
Here's your class update for today ({today_str}):

📚 Topic: {row.get('Topic', 'Not specified')}
🕒 Time: {row.get('Time', 'Not specified')}
👨‍🏫 Faculty: {row.get('Faculty', 'Not specified')}
🏫 Classroom: {row.get('Classroom', 'Not specified')}
📄 Handout: {row.get('Handout', 'Not available')}
🧪 Test Link: {row.get('test link', 'Not available')}
📺 Session Link: {row.get('session link', 'Not available')}

Best of luck!
— Team TIME
"""

                        # Send via WhatsApp
                        try:
                            twilio_client.messages.create(
                                body=message,
                                from_=twilio_number,
                                to=f"whatsapp:{mobile}"
                            )
                            print(f"✅ Sent message to {name} ({mobile})")
                        except Exception as e:
                            print(f"❌ Failed to send to {mobile}: {e}")

    except Exception as e:
        print(f"🔥 Critical error in notification system: {str(e)}")

def start_scheduler():
    """Initialize and start the scheduler"""
    scheduler = BlockingScheduler(timezone=pytz.timezone(os.getenv("TIMEZONE")))
    
    # Schedule to run every day at 8 AM
    scheduler.add_job(
        send_daily_notifications,
        'cron',
        hour=11,
        minute=17,
        name="daily_class_notifications"
    )
    
    print(f"⏰ Notification scheduler started. Will run daily at 8 AM {os.getenv('TIMEZONE')} time.")
    print("Press Ctrl+C to exit")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\nScheduler stopped gracefully")

if __name__ == '__main__':
    start_scheduler()