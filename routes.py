from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models import User, ProductMonitor, Notification
from scraper import scrape_product_info
from monitoring import start_monitoring_for_product
import logging

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/test')
def test_page():
    """Simple test page to verify the server is working"""
    with open('test_simple.html', 'r') as f:
        return f.read()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash('Please enter a username', 'error')
            return render_template('login.html')
        
        # Simulate guest login - create or get user
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email='')
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        flash(f'Welcome, {username}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    monitors = ProductMonitor.query.filter_by(user_id=user.id, is_active=True).all()
    
    return render_template('dashboard.html', user=user, monitors=monitors)

@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user for template rendering
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get form data
            product_url = request.form.get('product_url', '').strip()
            email = request.form.get('email', '').strip()
            notification_pref = request.form.get('notification_preference', 'email')
            phone_number = request.form.get('phone_number', '').strip() if notification_pref == 'email_whatsapp' else None
            
            # Monitoring conditions
            check_stock = request.form.get('check_stock') == 'on'
            check_size = request.form.get('check_size') == 'on'
            desired_size = request.form.get('desired_size', '').strip() if check_size else None
            check_delivery = request.form.get('check_delivery') == 'on'
            check_price = request.form.get('check_price') == 'on'
            target_price = float(request.form.get('target_price', 0)) if check_price and request.form.get('target_price') else None
            
            # Validation
            if not product_url:
                flash('Product URL is required', 'error')
                return render_template('monitor.html', user=user)
            
            if not email:
                flash('Email is required', 'error')
                return render_template('monitor.html', user=user)
            
            if notification_pref == 'email_whatsapp' and not phone_number:
                flash('Phone number is required for WhatsApp notifications', 'error')
                return render_template('monitor.html', user=user)
            
            if not any([check_stock, check_size, check_delivery, check_price]):
                flash('Please select at least one monitoring condition', 'error')
                return render_template('monitor.html', user=user)
            
            # Update user info
            user = User.query.get(session['user_id'])
            user.email = email
            user.phone_number = phone_number
            user.notification_preference = notification_pref
            
            # Scrape product info
            product_info = scrape_product_info(product_url)
            if not product_info:
                flash('Unable to scrape product information. Please check the URL.', 'error')
                return render_template('monitor.html', user=user)
            
            # Create monitor
            monitor = ProductMonitor(
                user_id=user.id,
                product_url=product_url,
                product_name=product_info.get('name', 'Unknown Product'),
                product_price=product_info.get('price', 'N/A'),
                check_stock=check_stock,
                check_size=check_size,
                desired_size=desired_size,
                check_delivery=check_delivery,
                check_price=check_price,
                target_price=target_price,
                last_status='Monitoring started'
            )
            
            db.session.add(monitor)
            db.session.commit()
            
            # Start monitoring
            start_monitoring_for_product(monitor.id)
            
            # Send confirmation message
            from notifications import send_monitoring_confirmation
            conditions = {
                'check_stock': check_stock,
                'check_size': check_size,
                'desired_size': desired_size,
                'check_delivery': check_delivery,
                'check_price': check_price,
                'target_price': target_price
            }
            
            confirmation_sent = send_monitoring_confirmation(
                email, phone_number, monitor.product_name, conditions, notification_pref
            )
            
            # Show success message regardless of confirmation status
            if confirmation_sent:
                flash('Product monitoring started successfully! Confirmation sent to your email/WhatsApp.', 'success')
            else:
                flash('Product monitoring started successfully! Check your dashboard for status updates.', 'success')
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logging.error(f"Error creating monitor: {str(e)}")
            flash('An error occurred while setting up monitoring. Please try again.', 'error')
            return render_template('monitor.html', user=user)
    
    return render_template('monitor.html', user=user)

@app.route('/stop_monitor/<int:monitor_id>')
def stop_monitor(monitor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    monitor = ProductMonitor.query.filter_by(id=monitor_id, user_id=session['user_id']).first()
    if monitor:
        monitor.is_active = False
        db.session.commit()
        flash('Monitoring stopped', 'info')
    else:
        flash('Monitor not found', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_monitor/<int:monitor_id>')
def delete_monitor(monitor_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    monitor = ProductMonitor.query.filter_by(id=monitor_id, user_id=session['user_id']).first()
    if monitor:
        db.session.delete(monitor)
        db.session.commit()
        flash('Monitor deleted', 'info')
    else:
        flash('Monitor not found', 'error')
    
    return redirect(url_for('dashboard'))
