# Zeek-Restaurent-Booking-Bot

A complete, production-ready WhatsApp chatbot built using **Flask**, **SQLite**, **Meta WhatsApp Cloud API**, and **Razorpay**. This bot allows restaurant customers to:

- View the Menu with Images, Ingredients, and Health Stats.
- Book Tables via WhatsApp.
- Make Payments securely via Razorpay.
- View Booking History.
- Enjoy a user-friendly WhatsApp button menu.
- Admin Dashboard for monitoring all bookings.
- Message customers directly from the Admin Panel.

---

## 🚀 Features

✅ Interactive WhatsApp buttons (Menu / Book Table / View History)  
✅ Beautiful menu display with images, ingredients & health info  
✅ Table Booking with slot limit (max 5 tables / 2hr slot)  
✅ Razorpay payment link generation (can be disabled for test)  
✅ Automatic Booking History tracking  
✅ Admin Panel (`/admin`) to view bookings  
✅ Message customers manually from `/send` page  
✅ Booking Session Timeout (10 min inactivity reset)  
✅ Prevent double booking on the same day  

---

## 📂 Project Structure

/templates
│ ├── admin.html # Admin Dashboard
│ └── send.html # Send Message Panel
│
app.py
db.sqlite3
requirements.txt 
Procfile
README.md 



---

## ⚙️ Setup Instructions

### 1. Clone the Repository

git clone https://github.com/YOUR_USERNAME/Zeek-Restaurent-Bot.git
cd Zeek-Restaurent-Bot

### 2. Create Virtual Environment & Install Dependencies

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### 3. Configure Meta & Razorpay Credentials in app.py

VERIFY_TOKEN = "YOUR_META_VERIFY_TOKEN" 
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID" 
WHATSAPP_TOKEN = "YOUR_META_ACCESS_TOKEN" 
razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY_ID", "YOUR_RAZORPAY_SECRET")) 

### 4. Initialize Database

python
from app import init_db
init_db()
exit()
### 5. Run Locally

python app.py
