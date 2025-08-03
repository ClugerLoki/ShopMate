// ShopMate - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-dismissible)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.parentNode) {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(function() {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 500);
            }
        }, 5000);
    });
    
    // Form validation helpers
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            // Add loading state to submit buttons
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
                
                // Re-enable after 10 seconds as fallback
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 10000);
            }
        });
    });
    
    // URL validation for product URL input
    const productUrlInput = document.getElementById('product_url');
    if (productUrlInput) {
        productUrlInput.addEventListener('blur', function() {
            const url = this.value.trim();
            if (url && !isValidURL(url)) {
                this.setCustomValidity('Please enter a valid URL starting with http:// or https://');
                this.classList.add('is-invalid');
            } else {
                this.setCustomValidity('');
                this.classList.remove('is-invalid');
                if (url) {
                    this.classList.add('is-valid');
                }
            }
        });
    }
    
    // Phone number formatting
    const phoneInput = document.getElementById('phone_number');
    if (phoneInput) {
        phoneInput.addEventListener('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value && !value.startsWith('+')) {
                value = '+' + value;
            }
            this.value = value;
        });
    }
    
    // Notification preference handling
    const emailOnlyRadio = document.getElementById('email_only');
    const emailWhatsAppRadio = document.getElementById('email_whatsapp');
    const phoneInputDiv = document.getElementById('phone_input');
    
    if (emailOnlyRadio && emailWhatsAppRadio && phoneInputDiv) {
        function toggleNotificationInputs() {
            if (emailWhatsAppRadio.checked) {
                phoneInputDiv.style.display = 'block';
                const phoneNumberInput = document.getElementById('phone_number');
                if (phoneNumberInput) {
                    phoneNumberInput.required = true;
                }
            } else {
                phoneInputDiv.style.display = 'none';
                const phoneNumberInput = document.getElementById('phone_number');
                if (phoneNumberInput) {
                    phoneNumberInput.required = false;
                }
            }
        }
        
        emailOnlyRadio.addEventListener('change', toggleNotificationInputs);
        emailWhatsAppRadio.addEventListener('change', toggleNotificationInputs);
        
        // Initialize on page load
        toggleNotificationInputs();
    }
    
    // Refresh dashboard every 60 seconds if on dashboard page
    if (window.location.pathname === '/dashboard' || window.location.pathname === '/') {
        setInterval(function() {
            // Only refresh if user is still on the page
            if (!document.hidden) {
                window.location.reload();
            }
        }, 60000);
    }
});

// Utility functions
function isValidURL(string) {
    try {
        const url = new URL(string);
        return url.protocol === "http:" || url.protocol === "https:";
    } catch (_) {
        return false;
    }
}

// Confirmation dialogs for destructive actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Format price display
function formatPrice(price) {
    if (typeof price === 'number') {
        return '$' + price.toFixed(2);
    }
    return price;
}

// Format date display
function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Show loading state
function showLoading(element) {
    if (element) {
        element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
        element.disabled = true;
    }
}

// Hide loading state
function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}
