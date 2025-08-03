#!/usr/bin/env python3
"""
Demo script showing the WhatsApp confirmation message format
"""

def show_confirmation_message_demo():
    """Show what the confirmation message looks like"""
    
    # Sample product and conditions
    product_name = "Dennis Lingo Men's Casual Shirt - Green"
    conditions = {
        'check_stock': True,
        'check_size': True,
        'desired_size': 'L',
        'check_delivery': False,
        'check_price': True,
        'target_price': 1500.0
    }
    
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

    print("=" * 60)
    print("WHATSAPP CONFIRMATION MESSAGE PREVIEW")
    print("=" * 60)
    print(message)
    print("=" * 60)
    print("\nThis message will be sent to:")
    print("✓ Email (if SMTP credentials are configured)")
    print("✓ WhatsApp (if Twilio credentials are properly configured)")
    print("\nThe application now handles errors gracefully and won't crash")
    print("if notification services aren't available.")

if __name__ == "__main__":
    show_confirmation_message_demo()