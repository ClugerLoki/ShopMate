import requests
from bs4 import BeautifulSoup
import logging
import re
from urllib.parse import urlparse

def scrape_product_info(url):
    """
    Scrape basic product information from a given URL
    Returns dict with name, price, availability info
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract product name (common selectors)
        name = None
        name_selectors = [
            'h1[data-testid="product-title"]',
            'h1.product-title',
            'h1#product-title',
            '.product-name h1',
            '.product-title',
            'h1',
            '.title h1',
            '[data-cy="product-name"]'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                name = element.get_text(strip=True)
                break
        
        # Extract price (common selectors)
        price = None
        price_selectors = [
            '.price',
            '.product-price',
            '[data-testid="price"]',
            '.current-price',
            '.sale-price',
            '.regular-price',
            '.price-current',
            '[class*="price"]'
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract price with regex
                price_match = re.search(r'[\$£€¥₹]\s*[\d,]+\.?\d*', price_text)
                if price_match:
                    price = price_match.group()
                    break
        
        # Check availability (common indicators)
        availability = check_availability(soup)
        
        # Check sizes available
        sizes = extract_available_sizes(soup)
        
        # Check delivery info
        delivery_info = extract_delivery_info(soup)
        
        return {
            'name': name or 'Unknown Product',
            'price': price or 'Price not found',
            'availability': availability,
            'sizes': sizes,
            'delivery': delivery_info,
            'url': url
        }
        
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

def check_availability(soup):
    """Check if product is in stock"""
    # Common out of stock indicators
    out_of_stock_indicators = [
        'out of stock',
        'sold out',
        'not available',
        'unavailable',
        'temporarily out of stock',
        'currently unavailable'
    ]
    
    # Check button text
    buttons = soup.find_all(['button', 'input'])
    for button in buttons:
        text = button.get_text(strip=True).lower()
        for indicator in out_of_stock_indicators:
            if indicator in text:
                return 'Out of Stock'
    
    # Check for availability messages
    availability_selectors = [
        '.availability',
        '.stock-status',
        '.product-availability',
        '[data-testid="availability"]'
    ]
    
    for selector in availability_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True).lower()
            for indicator in out_of_stock_indicators:
                if indicator in text:
                    return 'Out of Stock'
    
    return 'In Stock'

def extract_available_sizes(soup):
    """Extract available sizes"""
    sizes = []
    
    # Common size selectors
    size_selectors = [
        '.size-option',
        '.size-selector option',
        '.sizes button',
        '[data-testid="size-option"]',
        '.size-variant'
    ]
    
    for selector in size_selectors:
        elements = soup.select(selector)
        for element in elements:
            if element.name == 'option' and element.get('value'):
                size = element.get('value')
            else:
                size = element.get_text(strip=True)
            
            if size and size not in sizes:
                sizes.append(size)
    
    return sizes

def extract_delivery_info(soup):
    """Extract delivery information"""
    delivery_selectors = [
        '.delivery-info',
        '.shipping-info',
        '.delivery-options',
        '[data-testid="delivery"]'
    ]
    
    for selector in delivery_selectors:
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
    
    return 'Delivery info not found'

def check_product_conditions(monitor):
    """
    Check if current product state matches user's desired conditions
    Returns (should_notify, message)
    """
    try:
        product_info = scrape_product_info(monitor.product_url)
        if not product_info:
            return False, "Unable to check product"
        
        notifications = []
        
        # Check stock
        if monitor.check_stock and product_info['availability'] == 'In Stock':
            notifications.append("✅ Product is now in stock!")
        
        # Check size availability
        if monitor.check_size and monitor.desired_size:
            if monitor.desired_size in product_info.get('sizes', []):
                notifications.append(f"✅ Size {monitor.desired_size} is available!")
        
        # Check delivery (basic check)
        if monitor.check_delivery:
            delivery_text = product_info.get('delivery', '').lower()
            if 'available' in delivery_text or 'delivery' in delivery_text:
                notifications.append("✅ Delivery is available!")
        
        # Check price
        if monitor.check_price and monitor.target_price:
            price_text = product_info.get('price', '')
            current_price = extract_price_number(price_text)
            if current_price and current_price <= monitor.target_price:
                notifications.append(f"✅ Price dropped to {price_text} (target: ${monitor.target_price})")
        
        if notifications:
            message = f"Good news about {product_info['name']}!\n\n" + "\n".join(notifications)
            return True, message
        
        return False, "Conditions not yet met"
        
    except Exception as e:
        logging.error(f"Error checking conditions for monitor {monitor.id}: {str(e)}")
        return False, f"Error checking product: {str(e)}"

def extract_price_number(price_text):
    """Extract numeric price from price text"""
    try:
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
    except:
        pass
    return None
