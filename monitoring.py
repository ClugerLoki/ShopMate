import threading
import time
import logging
from datetime import datetime
from app import app, db
from models import ProductMonitor, User
from scraper import check_product_conditions
from notifications import send_notification

# Global dictionary to store monitoring threads
monitoring_threads = {}

def monitor_product(monitor_id):
    """Monitor a single product continuously"""
    with app.app_context():
        while True:
            try:
                monitor = ProductMonitor.query.get(monitor_id)
                if not monitor or not monitor.is_active:
                    break
                
                user = User.query.get(monitor.user_id)
                if not user:
                    break
                
                # Check product conditions
                should_notify, message = check_product_conditions(monitor)
                
                # Update last checked time
                monitor.last_checked = datetime.utcnow()
                monitor.last_status = message
                
                if should_notify:
                    # Send notification
                    if send_notification(user, monitor, message):
                        logging.info(f"Notification sent for monitor {monitor_id}")
                        # Stop monitoring after successful notification
                        monitor.is_active = False
                    else:
                        logging.error(f"Failed to send notification for monitor {monitor_id}")
                
                db.session.commit()
                
                # Wait 5 minutes before next check
                time.sleep(300)
                
            except Exception as e:
                logging.error(f"Error in monitoring thread for monitor {monitor_id}: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying
        
        # Clean up thread reference
        if monitor_id in monitoring_threads:
            del monitoring_threads[monitor_id]

def start_monitoring_for_product(monitor_id):
    """Start monitoring for a specific product"""
    if monitor_id in monitoring_threads:
        logging.info(f"Monitor {monitor_id} is already being monitored")
        return
    
    thread = threading.Thread(target=monitor_product, args=(monitor_id,), daemon=True)
    thread.start()
    monitoring_threads[monitor_id] = thread
    logging.info(f"Started monitoring for product {monitor_id}")

def start_all_active_monitoring():
    """Start monitoring for all active monitors on app startup"""
    with app.app_context():
        active_monitors = ProductMonitor.query.filter_by(is_active=True).all()
        for monitor in active_monitors:
            start_monitoring_for_product(monitor.id)
        logging.info(f"Started monitoring for {len(active_monitors)} active monitors")

# Start monitoring when module is imported
start_all_active_monitoring()
