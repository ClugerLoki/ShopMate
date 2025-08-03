import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import logging

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")

def send_email_notification(to_email, subject, message):
    """Send email notification"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logging.error("Email credentials not configured")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message, 'plain'))
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Enable security
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        text = msg.as_string()
        server.sendmail(SMTP_USERNAME, to_email, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

def send_whatsapp_notification(to_phone, message):
    """Send WhatsApp notification via Twilio"""
    try:
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            logging.warning("Twilio credentials not configured - skipping WhatsApp notification")
            return False
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Clean phone numbers
        to_phone_clean = to_phone.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        from_phone_clean = TWILIO_PHONE_NUMBER.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        
        # Ensure proper formatting for international numbers
        if not to_phone_clean.startswith('1') and len(to_phone_clean) == 10:
            to_phone_clean = '1' + to_phone_clean  # Add US country code if missing
        if not from_phone_clean.startswith('1') and len(from_phone_clean) == 10:
            from_phone_clean = '1' + from_phone_clean
        
        # For Twilio WhatsApp, the from number needs to be exactly as configured in Twilio
        # Try different formats to find the working one
        formats_to_try = [
            # Twilio WhatsApp Sandbox number (most common)
            ('whatsapp:+14155238886', f'whatsapp:+{to_phone_clean}'),
            # User's configured WhatsApp number
            (f'whatsapp:+{from_phone_clean}', f'whatsapp:+{to_phone_clean}'),
            # Alternative sandbox numbers
            ('whatsapp:+15017122661', f'whatsapp:+{to_phone_clean}'),
            # Direct format with user's number
            (TWILIO_PHONE_NUMBER, f'whatsapp:+{to_phone_clean}'),
        ]
        
        last_error = None
        for from_format, to_format in formats_to_try:
            try:
                message_obj = client.messages.create(
                    body=message,
                    from_=from_format,
                    to=to_format
                )
                logging.info(f"WhatsApp message sent successfully. SID: {message_obj.sid}")
                return True
            except Exception as format_error:
                last_error = format_error
                continue
        
        # If all formats failed, log the last error
        raise last_error
        
    except Exception as e:
        error_str = str(e)
        if "63007" in error_str:
            logging.warning("WhatsApp sandbox not configured. To enable WhatsApp notifications:")
            logging.warning("1. Go to Twilio Console > Messaging > Try it out > Send a WhatsApp message")
            logging.warning("2. Follow the sandbox setup instructions")
            logging.warning("3. Add your phone number to the sandbox")
        elif "21910" in error_str:
            logging.warning("WhatsApp channel mismatch. Make sure TWILIO_PHONE_NUMBER is your WhatsApp-enabled number")
        else:
            logging.warning(f"WhatsApp notification failed: {error_str}")
        return False

def send_monitoring_confirmation(email, phone_number, product_name, conditions, notification_pref):
    """Send confirmation message when monitoring starts"""
    try:
        # Create conditions summary
        conditions_list = []
        if conditions.get('check_stock'):
            conditions_list.append("Stock availability")
        if conditions.get('check_size') and conditions.get('desired_size'):
            conditions_list.append(f"Size: {conditions['desired_size']}")
        if conditions.get('check_delivery'):
            conditions_list.append("Delivery status")
        if conditions.get('check_price') and conditions.get('target_price'):
            conditions_list.append(f"Price drops below ₹{conditions['target_price']}")
        
        conditions_text = ", ".join(conditions_list) if conditions_list else "General monitoring"
        
        # Create confirmation message
        message = f"""🛍️ ShopMate Monitoring Started!

Product: {product_name}

Monitoring for: {conditions_text}

We'll notify you as soon as your conditions are met. You can check your dashboard anytime to see the status.

Happy shopping! 🎉"""

        # Send email confirmation
        email_sent = send_email_notification(
            email, 
            "ShopMate - Monitoring Started", 
            message
        )
        
        # Send WhatsApp confirmation if requested
        whatsapp_sent = True
        if notification_pref == 'email_whatsapp' and phone_number:
            whatsapp_sent = send_whatsapp_notification(phone_number, message)
            # Don't fail the whole confirmation if WhatsApp fails
            if not whatsapp_sent:
                logging.info("WhatsApp confirmation failed, but email should work")
        
        # Return True if at least email credentials exist, even if WhatsApp fails
        return email_sent or (SMTP_USERNAME and SMTP_PASSWORD)
        
    except Exception as e:
        logging.error(f"Failed to send monitoring confirmation: {str(e)}")
        return False

def send_notification(user, monitor, message):
    """Send notification based on user preference"""
    from app import db
    from models import Notification
    
    try:
        subject = f"Product Alert: {monitor.product_name}"
        
        # Always send email
        email_success = send_email_notification(user.email, subject, message)
        
        if email_success:
            # Log email notification
            email_notif = Notification(
                monitor_id=monitor.id,
                notification_type='email',
                message=message,
                status='sent'
            )
            db.session.add(email_notif)
        
        # Send WhatsApp if preference is set and phone number exists
        whatsapp_success = True  # Default to True if WhatsApp not needed
        if user.notification_preference == 'email_whatsapp' and user.phone_number:
            whatsapp_success = send_whatsapp_notification(user.phone_number, message)
            
            # Log WhatsApp notification attempt
            whatsapp_notif = Notification(
                monitor_id=monitor.id,
                notification_type='whatsapp',
                message=message,
                status='sent' if whatsapp_success else 'failed'
            )
            db.session.add(whatsapp_notif)
            
            if whatsapp_success:
                logging.info(f"WhatsApp notification sent successfully for monitor {monitor.id}")
            else:
                logging.warning(f"WhatsApp notification failed for monitor {monitor.id}")
        
        db.session.commit()
        
        # Return True if email succeeded (WhatsApp failure shouldn't stop the notification process)
        # But we still want to try WhatsApp if it's requested
        return email_success
        
    except Exception as e:
        logging.error(f"Error sending notification: {str(e)}")
        return False
