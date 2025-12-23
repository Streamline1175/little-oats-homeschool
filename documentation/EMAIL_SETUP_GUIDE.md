# 📧 Custom Email Setup Guide - Little Oat Learners

## Overview

Your customers will now receive beautiful, branded order confirmation emails with complete itemized product lists - matching your Little Oat Learners theme!

---

## 🎨 What Customers Will Receive

### Email Features:
- ✅ **Beautiful Design** - Matches your website theme
- ✅ **Itemized Product List** - Shows every item purchased
- ✅ **Order Details** - Order number, date, total
- ✅ **Next Steps** - Clear instructions on what happens next
- ✅ **Branded** - Your logo, colors, and messaging
- ✅ **Mobile Responsive** - Looks great on all devices

### Email Preview:
```
┌─────────────────────────────────────┐
│  [Little Oat Logo]                  │
│                                     │
│         Thank You!                  │
│  Your order has been confirmed      │
│                                     │
│            ✓                        │
│                                     │
│  Hi John,                           │
│  Thank you for your purchase!...    │
│                                     │
│  Order Details                      │
│  Order Number: #123456              │
│  Order Date: December 23, 2025      │
│                                     │
│  Items Purchased                    │
│  • Premium License - $79.99         │
│  • Math Bundle - $29.00             │
│  • Reading Pack - $24.00            │
│  ─────────────────────────           │
│  Total: $77.00                      │
│                                     │
│  What happens next?                 │
│  ✓ Download links being prepared    │
│  ✓ Separate email with access       │
│  ✓ Save this for your records       │
│                                     │
│  [Visit Our Website]                │
│                                     │
│  Questions? We're here to help!     │
│  support@littleoatlearners.com      │
└─────────────────────────────────────┘
```

---

## 🚀 Setup Instructions

### Step 1: Create SendGrid Account (Free)

1. **Go to SendGrid**:
   - Visit: https://signup.sendgrid.com/
   - Sign up for free account (100 emails/day free forever)

2. **Verify your email**:
   - Check your inbox for verification email
   - Click the verification link

3. **Complete sender verification**:
   - Go to Settings → Sender Authentication
   - Verify a single sender email (e.g., orders@littleoatlearners.com)
   - OR verify your domain (recommended for production)

### Step 2: Get API Key

1. **Create API key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Name: "Little Oat Orders"
   - Permissions: "Full Access" (or "Mail Send" only)
   - Click "Create & View"

2. **Copy the API key**:
   - ⚠️ **IMPORTANT:** Copy it now! You won't see it again
   - Save it somewhere safe temporarily

### Step 3: Configure RPI

1. **SSH into your RPI**:
   ```bash
   ssh pi@your-rpi-address
   cd /path/to/your/fastapi/project
   ```

2. **Install SendGrid**:
   ```bash
   pip install sendgrid
   ```

3. **Update `.env` file**:
   ```bash
   nano .env
   ```
   
   Add these lines:
   ```bash
   SENDGRID_API_KEY=SG.your_api_key_here
   FROM_EMAIL=orders@littleoatlearners.com
   ```
   
   Save and exit (Ctrl+O, Enter, Ctrl+X)

4. **Upload email sender module**:
   ```bash
   # From your local machine
   scp rpi-backend/email_sender.py pi@your-rpi:/path/to/project/email_sender.py
   ```

5. **Upload email template** (optional - inline template is included as fallback):
   ```bash
   # Create directory
   ssh pi@your-rpi "mkdir -p /path/to/project/email-templates"
   
   # Upload template
   scp email-templates/order-confirmation.html pi@your-rpi:/path/to/project/email-templates/
   ```

6. **Upload updated main.py**:
   ```bash
   scp rpi-backend/main.py pi@your-rpi:/path/to/project/main.py
   ```

7. **Restart service**:
   ```bash
   ssh pi@your-rpi
   sudo systemctl restart your-fastapi-service
   ```

---

## ✅ Testing

### Test 1: Verify SendGrid Configuration

```bash
# SSH into RPI
ssh pi@your-rpi
cd /path/to/project

# Test Python can import SendGrid
python3 -c "from sendgrid import SendGridAPIClient; print('✅ SendGrid installed')"
```

### Test 2: Send Test Email

Create a test script:
```bash
nano test_email.py
```

Paste this:
```python
import asyncio
from email_sender import send_order_confirmation_email

async def test():
    result = await send_order_confirmation_email(
        to_email="your-email@example.com",  # YOUR EMAIL HERE
        customer_name="Test Customer",
        order_id="TEST-123",
        items=[
            {"title": "Test Product 1", "price": "$29.00"},
            {"title": "Test Product 2", "price": "$19.00"}
        ],
        total="$48.00"
    )
    print(f"Email sent: {result}")

asyncio.run(test())
```

Run it:
```bash
python3 test_email.py
```

Check your inbox! You should receive the beautiful order confirmation email.

### Test 3: Test via Webhook

1. **From Lemon Squeezy Dashboard**:
   - Go to Settings → Webhooks
   - Click your webhook
   - Click "Send Test"

2. **Check RPI logs**:
   ```bash
   sudo journalctl -u your-fastapi-service -f
   ```

3. **Look for**:
   ```
   📬 Received webhook: order_created
   📦 Order #123456 created
   👤 Customer: Test User (test@example.com)
   💰 Total: $50.00
   📋 Items: 2
   📝 Order contains:
      • Product 1 - $25.00
      • Product 2 - $25.00
   📧 Custom order confirmation email sent to test@example.com
   ✅ Order #123456 processed successfully
   ```

4. **Check email inbox** - Should receive the email!

### Test 4: Complete Purchase Flow

1. Add products to cart on website
2. Proceed to checkout
3. Complete purchase (use test mode if available)
4. Verify:
   - ✅ Redirected to thank-you page
   - ✅ Webhook received (check logs)
   - ✅ **Email received with itemized list** 📧
   - ✅ Email looks beautiful and branded

---

## 🎯 Email Flow

### When Customer Completes Purchase:

**1. Lemon Squeezy Checkout** (Immediate)
- Customer pays
- Sees itemized list on checkout page

**2. Thank-You Page** (Immediate)
- Redirected to your thank-you page
- Shows order summary

**3. Webhook Fires** (Within seconds)
- Your RPI receives order_created event
- Logs order details
- **Sends custom email** 📧

**4. Customer Receives Emails**:
- **Your Custom Email** (Within seconds) ✅
  - Beautiful branded design
  - Complete itemized list
  - Order details
  - Next steps
  
- **Lemon Squeezy Email** (Within minutes)
  - Default confirmation
  - May not show itemized list
  - Payment receipt

---

## 🔧 Customization

### Change Email Content

Edit `email-templates/order-confirmation.html`:

**Change greeting**:
```html
<p>Hi {{customer_name}},</p>
<p>Thank you for your purchase! ...</p>
```

**Change "What's Next" steps**:
```html
<li>Your download links are being prepared</li>
<li>You'll receive a separate email with access details</li>
```

**Change footer**:
```html
<p>Email us at <a href="mailto:support@littleoatlearners.com">support@littleoatlearners.com</a></p>
```

After editing, upload to RPI:
```bash
scp email-templates/order-confirmation.html pi@your-rpi:/path/to/project/email-templates/
```

### Change "From" Email

In `.env`:
```bash
FROM_EMAIL=hello@littleoatlearners.com
```

**Note:** Must be verified in SendGrid!

### Add Download Links

In `email_sender.py`, modify the template to include download links:

```python
# In build_items_html function, add download link:
items_html += f"""
<tr>
    <td>
        <div>{item.get('title')}</div>
        <a href="{item.get('download_url', '#')}" style="color: #7A8B6F;">Download</a>
    </td>
</tr>
```

---

## 📊 Monitoring

### View Email Logs

```bash
# Real-time
sudo journalctl -u your-fastapi-service -f | grep "📧"

# Last 50 emails
sudo journalctl -u your-fastapi-service | grep "📧" | tail -50
```

### SendGrid Dashboard

1. Go to https://app.sendgrid.com
2. Navigate to "Activity"
3. See all sent emails, opens, clicks, bounces

### Email Deliverability

**Best practices**:
- ✅ Verify your domain in SendGrid (not just single sender)
- ✅ Set up SPF and DKIM records
- ✅ Monitor bounce rates
- ✅ Keep "from" email consistent

---

## 🚨 Troubleshooting

### Email Not Sending

**Check 1: API Key**
```bash
# Verify API key is set
ssh pi@your-rpi
cat .env | grep SENDGRID_API_KEY
```

**Check 2: SendGrid Installed**
```bash
pip list | grep sendgrid
# Should show: sendgrid X.X.X
```

**Check 3: Logs**
```bash
sudo journalctl -u your-fastapi-service -n 100 | grep -A 5 "order_created"
```

Look for error messages.

**Check 4: SendGrid Activity**
- Go to SendGrid dashboard → Activity
- Check if email was sent
- Check for errors

### Email Goes to Spam

**Solutions**:
1. **Verify domain** in SendGrid (not just single sender)
2. **Set up SPF record**:
   ```
   v=spf1 include:sendgrid.net ~all
   ```
3. **Set up DKIM** in SendGrid settings
4. **Avoid spam trigger words** in subject/content
5. **Ask customers to whitelist** your email

### Wrong Email Template

**Check template path**:
```bash
ssh pi@your-rpi
ls -la /path/to/project/email-templates/order-confirmation.html
```

If missing, the inline template will be used (which is fine!).

### Customer Not Receiving Email

**Possible causes**:
1. Email in spam folder
2. Wrong email address
3. SendGrid daily limit reached (100/day on free tier)
4. Email bounced (check SendGrid activity)

---

## 💰 SendGrid Pricing

### Free Tier:
- ✅ 100 emails/day forever
- ✅ Perfect for starting out
- ✅ All features included

### Paid Tiers (if you grow):
- **Essentials**: $19.95/mo - 50,000 emails/month
- **Pro**: $89.95/mo - 100,000 emails/month

**Recommendation:** Start with free tier, upgrade when needed.

---

## 📁 File Structure

```
your-rpi-project/
├── main.py                          ← Updated with email sending
├── email_sender.py                  ← NEW - Email sending module
├── email-templates/                 ← NEW - Email templates
│   └── order-confirmation.html      ← Beautiful HTML template
├── .env                             ← Add SENDGRID_API_KEY
└── requirements.txt                 ← Add sendgrid
```

---

## 📝 Environment Variables Summary

Your `.env` should have:
```bash
# Lemon Squeezy
LEMON_SQUEEZY_API_KEY=your_key
LEMON_SQUEEZY_STORE_ID=your_store_id
LEMON_SQUEEZY_BUNDLE_VARIANT_ID=your_variant_id
LEMON_SQUEEZY_WEBHOOK_SECRET=your_webhook_secret

# SendGrid (NEW)
SENDGRID_API_KEY=SG.your_sendgrid_api_key
FROM_EMAIL=orders@littleoatlearners.com

# Ngrok (Optional)
NGROK_DOMAIN=your_domain
```

---

## ✅ Success Checklist

- [ ] SendGrid account created
- [ ] Sender email verified
- [ ] API key generated and saved
- [ ] `pip install sendgrid` on RPI
- [ ] `SENDGRID_API_KEY` added to `.env`
- [ ] `FROM_EMAIL` added to `.env`
- [ ] `email_sender.py` uploaded to RPI
- [ ] Email template uploaded (optional)
- [ ] `main.py` updated and uploaded
- [ ] Service restarted
- [ ] Test email sent successfully
- [ ] Webhook test successful
- [ ] Complete purchase test successful
- [ ] Customer received beautiful email ✅

---

## 🎉 You're Done!

Customers now receive:
1. ✅ Itemized list on checkout page
2. ✅ Beautiful thank-you page
3. ✅ **Custom branded email with full order details** 📧
4. ✅ Lemon Squeezy receipt (backup)

**Total setup time:** ~20 minutes

**Result:** Professional, branded customer experience that builds trust and looks amazing! 🎨

---

## 📚 Additional Resources

- **SendGrid Docs**: https://docs.sendgrid.com/
- **Email Best Practices**: https://sendgrid.com/blog/email-best-practices/
- **HTML Email Guide**: https://www.campaignmonitor.com/css/

---

**Questions?** Check SendGrid activity dashboard or RPI logs for detailed error messages!
