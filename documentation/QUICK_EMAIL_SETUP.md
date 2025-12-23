# 🚀 Quick Email Setup - 20 Minutes

## What You're Adding

Custom branded order confirmation emails with itemized product lists - sent automatically when customers make a purchase!

---

## ⚡ 4-Step Setup

### Step 1: Create SendGrid Account (5 min)

1. Go to https://signup.sendgrid.com/
2. Sign up (free - 100 emails/day)
3. Verify your email
4. Verify sender: Settings → Sender Authentication
   - Use: `orders@littleoatlearners.com`
5. Create API key: Settings → API Keys
   - Name: "Little Oat Orders"
   - Permission: "Full Access"
   - **Copy the key!** (You won't see it again)

---

### Step 2: Install & Configure (5 min)

```bash
# SSH into RPI
ssh pi@your-rpi
cd /path/to/your/project

# Install SendGrid
pip install sendgrid

# Update .env
nano .env
```

Add these lines to `.env`:
```bash
SENDGRID_API_KEY=SG.your_api_key_here
FROM_EMAIL=orders@littleoatlearners.com
```

Save and exit (Ctrl+O, Enter, Ctrl+X)

---

### Step 3: Upload Files (5 min)

From your local machine:

```bash
# Upload email sender module
scp rpi-backend/email_sender.py pi@your-rpi:/path/to/project/

# Upload updated main.py
scp rpi-backend/main.py pi@your-rpi:/path/to/project/

# (Optional) Upload email template
ssh pi@your-rpi "mkdir -p /path/to/project/email-templates"
scp email-templates/order-confirmation.html pi@your-rpi:/path/to/project/email-templates/
```

---

### Step 4: Restart & Test (5 min)

```bash
# Restart service
ssh pi@your-rpi
sudo systemctl restart your-fastapi-service

# Check it's running
sudo systemctl status your-fastapi-service
```

**Test it:**
```bash
# Create test script
nano test_email.py
```

Paste:
```python
import asyncio
from email_sender import send_order_confirmation_email

async def test():
    await send_order_confirmation_email(
        to_email="YOUR_EMAIL@example.com",  # Change this!
        customer_name="Test Customer",
        order_id="TEST-123",
        items=[
            {"title": "Test Product 1", "price": "$29.00"},
            {"title": "Test Product 2", "price": "$19.00"}
        ],
        total="$48.00"
    )

asyncio.run(test())
```

Run:
```bash
python3 test_email.py
```

**Check your inbox!** You should receive a beautiful branded email! 📧

---

## ✅ Verification Checklist

- [ ] SendGrid account created
- [ ] API key copied
- [ ] SendGrid installed on RPI (`pip install sendgrid`)
- [ ] `.env` updated with `SENDGRID_API_KEY` and `FROM_EMAIL`
- [ ] Files uploaded (`email_sender.py`, `main.py`)
- [ ] Service restarted
- [ ] Test email received successfully
- [ ] Email looks beautiful and branded

---

## 🎯 What Happens Now

### When Customer Purchases:

**1. Checkout** → Sees itemized list

**2. Thank-You Page** → Sees order confirmation

**3. Webhook Fires** → Your RPI receives order

**4. Email Sent** → Customer receives:
```
┌─────────────────────────────────┐
│  [Little Oat Logo]              │
│                                 │
│       Thank You!                │
│  Your order has been confirmed  │
│                                 │
│  Hi John,                       │
│  Thank you for your purchase!   │
│                                 │
│  Order #123456                  │
│  December 23, 2025              │
│                                 │
│  Items Purchased:               │
│  • Premium License - $79.99     │
│  • Math Bundle - $29.00         │
│  • Reading Pack - $24.00        │
│  ─────────────────────          │
│  Total: $77.00                  │
│                                 │
│  [Visit Our Website]            │
└─────────────────────────────────┘
```

---

## 🔍 Quick Troubleshooting

**Email not sending?**
```bash
# Check logs
sudo journalctl -u your-service -f | grep "📧"
```

**Wrong API key?**
```bash
# Verify .env
cat .env | grep SENDGRID
```

**SendGrid not installed?**
```bash
pip list | grep sendgrid
```

---

## 📚 Full Documentation

For detailed setup, customization, and troubleshooting:
- **`EMAIL_SETUP_GUIDE.md`** - Complete guide

---

## 🎉 Done!

**Total time:** ~20 minutes

**Result:** Customers receive beautiful, branded emails with complete order details!

**Free tier:** 100 emails/day (plenty to start!)

---

**Next:** Test a real purchase to see the complete flow! 🚀
