from flask import Flask, request, jsonify, render_template, redirect, url_for
import sqlite3
import json
import datetime
import requests
import razorpay

app = Flask(__name__)

VERIFY_TOKEN = ""#Your Coustom Token From Meta

razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY_ID", "YOUR_RAZORPAY_SECRET"))
booking_state = {}
MAX_TABLES = 5
SESSION_TIMEOUT_MINUTES = 10
PHONE_NUMBER_ID = ''#Number ID From Meta
WHATSAPP_TOKEN = ''#Access Token From Meta

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification token mismatch", 403

menu_items = {
    "pizza": {"price": 500, "ingredients": "Cheese, Tomato, Basil", "health": "300 kcal", "image": "https://example.com/pizza.jpg"},
    "burger": {"price": 300, "ingredients": "Beef Patty, Lettuce, Cheese", "health": "500 kcal", "image": "https://example.com/burger.jpg"},
    "pasta": {"price": 400, "ingredients": "Pasta, Cream, Garlic", "health": "450 kcal", "image": "https://example.com/pasta.jpg"}
}

def init_db():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY,
                    phone TEXT,
                    name TEXT,
                    date TEXT,
                    time TEXT,
                    people INTEGER,
                    paid TEXT,
                    razorpay_order_id TEXT
                )''')
    conn.commit()
    conn.close()

init_db()



def send_whatsapp_text(phone, message):                                            #To Show Api Error In Console
    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {WHATSAPP_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("WhatsApp API Response:", response.status_code, response.text)


def send_main_menu(phone):                                                         #Main Menu
    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
    headers = {'Authorization': f'Bearer {WHATSAPP_TOKEN}', 'Content-Type': 'application/json'}
    payload = {
      "messaging_product": "whatsapp",
      "to": phone,
      "type": "interactive",
      "interactive": {
        "type": "button",
        "body": {"text": "Main Menu:"},
        "action": {
          "buttons": [
            {"type": "reply", "reply": {"id": "menu_option", "title": "Menu"}},
            {"type": "reply", "reply": {"id": "book_table", "title": "Book Table"}},
            {"type": "reply", "reply": {"id": "view_history", "title": "View History"}}
          ]
        }
      }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_booking_alert(phone):                                                    #Alert System 
    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
    headers = {'Authorization': f'Bearer {WHATSAPP_TOKEN}', 'Content-Type': 'application/json'}
    payload = {
      "messaging_product": "whatsapp",
      "to": phone,
      "type": "interactive",
      "interactive": {
        "type": "button",
        "body": {"text": "⚠️ You already have a booking today. Choose:"},
        "action": {
          "buttons": [
            {"type": "reply", "reply": {"id": "cancel_booking", "title": "❌ Cancel"}},
            {"type": "reply", "reply": {"id": "continue_booking", "title": "🆕 Book Another"}},
            {"type": "reply", "reply": {"id": "back_to_menu", "title": "🔙 Back"}}
          ]
        }
      }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_image(phone, image_url, caption):
    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
    headers = {'Authorization': f'Bearer {WHATSAPP_TOKEN}', 'Content-Type': 'application/json'}
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "image",
        "image": {"link": image_url, "caption": caption}
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def is_session_expired(state_time):
    return (datetime.datetime.now() - state_time).total_seconds() > SESSION_TIMEOUT_MINUTES * 60

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Incoming WhatsApp Data:", json.dumps(data, indent=2))  # Debug print to console

    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get('messages')

        if messages:
            phone = messages[0]['from']  # Sender's WhatsApp number
            msg = messages[0]['text']['body'].lower()  # Message body
            now = datetime.datetime.now()

            print(f"Received message from {phone}: {msg}")

            if msg in menu_items:
                item = menu_items[msg]
                send_image(phone, item['image'],
                           f"{msg.title()} 🍽️\nPrice: ₹{item['price']}\nIngredients: {item['ingredients']}\nHealth: {item['health']}\n🔙 Back to Menu")
                return "OK"

            if phone in booking_state and is_session_expired(booking_state[phone]['time']):
                booking_state.pop(phone)
                send_whatsapp_text(phone, "⏳ Session expired. Starting again.")
                send_main_menu(phone)
                return "OK"

            if msg in ['menu_option', 'Menu']:
                reply = ""
                for item, d in menu_items.items():
                    reply += f"\n🍽️ {item.title()} - ₹{d['price']}\n{d['image']}"
                send_whatsapp_text(phone, reply)
                return "OK"

            elif msg in ['view_history', 'View History']:
                conn = sqlite3.connect('db.sqlite3')
                c = conn.cursor()
                c.execute("SELECT * FROM bookings WHERE phone=?", (phone,))
                bookings = c.fetchall()
                text = "Your Bookings:\n" + "\n".join([f"{b[2]} on {b[3]} at {b[4]} for {b[5]} - Paid: {b[6]}" for b in bookings])
                send_whatsapp_text(phone, text)
                conn.close()
                return "OK"

            elif msg in ['book_table', 'Book Table']:
                conn = sqlite3.connect('db.sqlite3')
                c = conn.cursor()
                today = now.strftime("%Y-%m-%d")
                c.execute("SELECT * FROM bookings WHERE phone=? AND date=?", (phone, today))
                existing = c.fetchone()
                conn.close()
                if existing:
                    send_booking_alert(phone)
                else:
                    booking_state[phone] = {"step": "name", "time": now}
                    send_whatsapp_text(phone, "Enter your Name:")
                return "OK"

            elif msg == 'cancel_booking':
                conn = sqlite3.connect('db.sqlite3')
                c = conn.cursor()
                today = now.strftime("%Y-%m-%d")
                c.execute("UPDATE bookings SET paid='Cancelled' WHERE phone=? AND date=?", (phone, today))
                conn.commit()
                conn.close()
                send_whatsapp_text(phone, "✅ Booking cancelled.")
                send_main_menu(phone)
                return "OK"

            elif msg == 'continue_booking':
                booking_state[phone] = {"step": "name", "time": now}
                send_whatsapp_text(phone, "Enter your Name:")
                return "OK"

            elif msg == 'back_to_menu':
                booking_state.pop(phone, None)
                send_main_menu(phone)
                return "OK"

            elif phone in booking_state:
                state = booking_state[phone]
                state['time'] = now
                if state['step'] == 'name':
                    state['name'] = msg
                    state['step'] = 'date'
                    send_whatsapp_text(phone, "Enter Date (YYYY-MM-DD):")
                elif state['step'] == 'date':
                    state['date'] = msg
                    state['step'] = 'time'
                    send_whatsapp_text(phone, "Enter Time (HH:MM):")
                elif state['step'] == 'time':
                    state['time_slot'] = msg
                    state['step'] = 'people'
                    send_whatsapp_text(phone, "Enter Number of People:")
                elif state['step'] == 'people':
                    state['people'] = int(msg)
                    conn = sqlite3.connect('db.sqlite3')
                    c = conn.cursor()
                    booking_dt = datetime.datetime.strptime(f"{state['date']} {state['time_slot']}", "%Y-%m-%d %H:%M")
                    lower = (booking_dt - datetime.timedelta(hours=2)).strftime("%H:%M")
                    upper = (booking_dt + datetime.timedelta(hours=2)).strftime("%H:%M")
                    c.execute('''SELECT COUNT(*) FROM bookings WHERE date=? AND time BETWEEN ? AND ? AND paid != 'Cancelled' ''',
                              (state['date'], lower, upper))
                    count = c.fetchone()[0]
                    if count >= MAX_TABLES:
                        send_whatsapp_text(phone, "❌ Slot full. Try another time.")
                        booking_state.pop(phone)
                    else:
                        order = razorpay_client.order.create({"amount": 50000, "currency": "INR", "payment_capture": 1})
                        c.execute("INSERT INTO bookings (phone, name, date, time, people, paid, razorpay_order_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                  (phone, state['name'], state['date'], state['time_slot'], state['people'], 'Pending', order['id']))
                        conn.commit()
                        send_whatsapp_text(phone, f"Pay ₹500: https://yourdomain.com/payment/{order['id']}")
                        booking_state.pop(phone)

                return "OK"

            else:
                send_main_menu(phone)
                return "OK"

        else:
            print("No messages in the incoming webhook.")
            return "No message received", 200

    except Exception as e:
        print("Error handling webhook:", str(e))
        return "Error", 500
@app.route('/admin')
def admin():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    c.execute("SELECT * FROM bookings")
    bookings = c.fetchall()
    conn.close()
    return render_template('admin.html', bookings=bookings)
from flask import Flask, request, render_template, redirect, url_for

@app.route('/send', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        phone = request.form['phone']
        message = request.form['message']
        send_whatsapp_text(phone, message)
        return f"✅ Message sent to {phone}!"
    return render_template('send.html')


if __name__ == '__main__':
    app.run(debug=True)
