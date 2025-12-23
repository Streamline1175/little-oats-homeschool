"""
Email sending module for Little Oat Learners
Handles order confirmation emails with beautiful HTML templates
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from datetime import datetime
from typing import List, Dict

def load_email_template() -> str:
    """Load the HTML email template"""
    template_path = os.path.join(os.path.dirname(__file__), 'email-templates', 'order-confirmation.html')
    
    # If template file doesn't exist, use inline template
    if not os.path.exists(template_path):
        return get_inline_template()
    
    with open(template_path, 'r') as f:
        return f.read()

def get_inline_template() -> str:
    """Inline HTML template as fallback"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Confirmation - Little Oat Learners</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background-color: #F5F0E8;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 24px; box-shadow: 0 12px 40px rgba(44, 36, 22, 0.08); overflow: hidden;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(180deg, #E8DFD0 0%, #FFFFFF 100%); padding: 40px 40px 30px; text-align: center;">
                            <img src="https://littleoatlearners.com/assets/logo.png" alt="Little Oat Learners" style="width: 80px; height: 80px; border-radius: 16px; margin-bottom: 20px;">
                            <h1 style="margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 32px; color: #2C2416; font-weight: 600;">Thank You!</h1>
                            <p style="margin: 10px 0 0; font-size: 16px; color: #6B5F4F;">Your order has been confirmed</p>
                        </td>
                    </tr>
                    
                    <!-- Success Icon -->
                    <tr>
                        <td style="padding: 30px 40px 20px; text-align: center;">
                            <div style="width: 60px; height: 60px; margin: 0 auto; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;">
                                <span style="color: white; font-size: 32px; font-weight: bold;">✓</span>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <p style="margin: 0; font-size: 16px; color: #4A4035; line-height: 1.6;">
                                Hi {{customer_name}},
                            </p>
                            <p style="margin: 15px 0 0; font-size: 16px; color: #4A4035; line-height: 1.6;">
                                Thank you for your purchase! We're excited to help you on your homeschool journey. Your order has been confirmed and you'll receive your downloads shortly.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Order Details -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <table role="presentation" style="width: 100%; background: #F5F0E8; border-radius: 16px; padding: 24px;">
                                <tr>
                                    <td>
                                        <h2 style="margin: 0 0 20px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; color: #2C2416;">Order Details</h2>
                                        
                                        <table role="presentation" style="width: 100%; margin-bottom: 15px;">
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6B5F4F;">Order Number:</td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #2C2416; font-weight: 600; text-align: right;">#{{order_id}}</td>
                                            </tr>
                                            <tr>
                                                <td style="padding: 8px 0; font-size: 14px; color: #6B5F4F;">Order Date:</td>
                                                <td style="padding: 8px 0; font-size: 14px; color: #2C2416; font-weight: 600; text-align: right;">{{order_date}}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Items Purchased -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <h2 style="margin: 0 0 20px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; color: #2C2416;">Items Purchased</h2>
                            
                            <table role="presentation" style="width: 100%;">
                                {{items_list}}
                            </table>
                            
                            <!-- Total -->
                            <table role="presentation" style="width: 100%; margin-top: 20px; padding-top: 20px; border-top: 2px solid #E8DFD0;">
                                <tr>
                                    <td style="padding: 8px 0; font-size: 18px; color: #2C2416; font-weight: 700;">Total</td>
                                    <td style="padding: 8px 0; font-size: 18px; color: #5A6B4F; font-weight: 700; text-align: right;">{{total}}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Download Button (if available) -->
                    {{download_button}}
                    
                    <!-- What's Next -->
                    <tr>
                        <td style="padding: 0 40px 30px;">
                            <table role="presentation" style="width: 100%; background: linear-gradient(135deg, rgba(122, 139, 111, 0.05), rgba(122, 139, 111, 0.1)); border-radius: 16px; padding: 24px; border: 1px solid #9AAD8C;">
                                <tr>
                                    <td>
                                        <h3 style="margin: 0 0 15px; font-size: 18px; color: #5A6B4F; font-weight: 600;">What happens next?</h3>
                                        <ul style="margin: 0; padding: 0 0 0 20px; color: #4A4035; font-size: 14px; line-height: 1.8;">
                                            <li style="margin-bottom: 8px;">Your download links are being prepared</li>
                                            <li style="margin-bottom: 8px;">You'll receive a separate email with access details</li>
                                            <li style="margin-bottom: 8px;">Save this email for your records</li>
                                            <li>Need help? We're here for you!</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 0 40px 40px; text-align: center;">
                            <a href="https://littleoatlearners.com" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #7A8B6F 0%, #5A6B4F 100%); color: #FFFFFF; text-decoration: none; border-radius: 32px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 20px rgba(90, 107, 79, 0.25);">
                                Visit Our Website
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #F5F0E8; padding: 30px 40px; text-align: center; border-top: 1px solid #E8DFD0;">
                            <p style="margin: 0 0 10px; font-size: 14px; color: #6B5F4F;">
                                Questions? We're here to help!
                            </p>
                            <p style="margin: 0 0 20px; font-size: 14px; color: #6B5F4F;">
                                Email us at <a href="mailto:support@littleoatlearners.com" style="color: #7A8B6F; text-decoration: none;">support@littleoatlearners.com</a>
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #8B7355;">
                                © 2025 Little Oat Learners. Crafted with care for homeschool families.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

def build_items_html(items: List[Dict]) -> str:
    """Build HTML for itemized product list"""
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #E8DFD0;">
                <div style="font-size: 15px; color: #2C2416; font-weight: 600; margin-bottom: 4px;">
                    {item.get('title', 'Product')}
                </div>
            </td>
            <td style="padding: 12px 0; border-bottom: 1px solid #E8DFD0; text-align: right;">
                <div style="font-size: 15px; color: #5A6B4F; font-weight: 600;">
                    {item.get('price', '$0.00')}
                </div>
            </td>
        </tr>
        """
    return items_html

async def send_order_confirmation_email(
    to_email: str,
    customer_name: str,
    order_id: str,
    items: List[Dict],
    total: str,
    download_url: str = ""
) -> bool:
    """
    Send order confirmation email with itemized product list and download link
    
    Args:
        to_email: Customer's email address
        customer_name: Customer's name
        order_id: Order ID from Lemon Squeezy
        items: List of items purchased
        total: Total price formatted (e.g., "$77.00")
        download_url: URL to download purchased products
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    # Get SendGrid API key
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('FROM_EMAIL', 'orders@littleoatlearners.com')
    
    if not api_key:
        print("⚠️ SENDGRID_API_KEY not set. Email not sent.")
        return False
    
    try:
        # Load template
        template = load_email_template()
        
        # Build items HTML
        items_html = build_items_html(items)
        
        # Format order date
        order_date = datetime.now().strftime("%B %d, %Y")
        
        # Build download button HTML
        if download_url:
            download_button = f"""
            <tr>
                <td style="padding: 0 40px 30px; text-align: center;">
                    <a href="{download_url}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #FFFFFF; text-decoration: none; border-radius: 32px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 20px rgba(16, 185, 129, 0.25); margin-bottom: 10px;">
                        📥 Download Your Products
                    </a>
                    <p style="margin: 10px 0 0; font-size: 13px; color: #6B5F4F;">
                        Click the button above to access your downloads
                    </p>
                </td>
            </tr>
            """
        else:
            download_button = ""
        
        # Replace placeholders
        html_content = template.replace('{{customer_name}}', customer_name)
        html_content = html_content.replace('{{order_id}}', order_id)
        html_content = html_content.replace('{{order_date}}', order_date)
        html_content = html_content.replace('{{items_list}}', items_html)
        html_content = html_content.replace('{{total}}', total)
        html_content = html_content.replace('{{download_button}}', download_button)
        
        # Create email
        message = Mail(
            from_email=Email(from_email, "Little Oat Learners"),
            to_emails=To(to_email),
            subject=f'Order Confirmation #{order_id} - Little Oat Learners',
            html_content=Content("text/html", html_content)
        )
        
        # Send email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print(f"✅ Order confirmation email sent to {to_email}")
            return True
        else:
            print(f"⚠️ Email send returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
