from flask import Flask, request, render_template, redirect, url_for, jsonify
import sqlite3
import requests
import json
import datetime
import uuid
import hashlib
import re
from config import MERCHANT_KEY, MERCHANT_SALT, PAYU_BASE_URL , VERIFY_TOKEN
from db import init_db, get_db_connection, add_item, delete_item, get_all, booking_data, confirm_booking, check_booking, history_booking, item_data, insert_booking, update_booking_status
from wa import send_menu_list, send_whatsapp_text, send_main_menu, send_booking_alert, send_image, send_whatsapp_confirmation
app = Flask(__name__)

booking_state = {}
MAX_TABLES = 5
SESSION_TIMEOUT_MINUTES = 10
init_db()

# ===================== META VALIDATOR =========================
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification token mismatch", 403
# ===================== META VALIDATOR ENDS ====================

# ===================== MAIN DATA VALIDATOR ====================    
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    try:
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        messages = value.get('messages')

        if messages:
            phone = messages[0]['from']
            now = datetime.datetime.now()
            message_type = messages[0]['type']
            msg = ""
            if message_type == 'text':
                msg = messages[0]['text']['body'].lower()
            elif message_type == 'interactive':
                interactive_type = messages[0]['interactive']['type']
                if interactive_type == 'button_reply':
                    msg = messages[0]['interactive']['button_reply']['id']
                elif interactive_type == 'list_reply':
                    msg = messages[0]['interactive']['list_reply']['id']
            else:
                    msg = ""
            
            if msg.isdigit():
                item_id = int(msg)
                try:
                    row = item_data(item_id)
                    if row:
                        (title, price, image, ingredients, energy, fat, carbohydrates, protein, sodium, sugars, fiber) = row
                        caption = f"🍽️ Item: {title}\n💰 Price: ₹{price}\n🥗 Ingredients: {ingredients}\n\n Health Stats per Slice (approx 100g):\n\t\t🔥 Energy: {energy}\n\t\t🥓 Fat: {fat}\n\t\t🍞 Carbohydrates: {carbohydrates}\n\t\t🧀 Protein: {protein}\n\t\t🧂 Sodium: {sodium}\n\t\t🍬 Sugars: {sugars}\n\t\t🌱 Fiber: {fiber}\n\n\n\n Reply Menu To Go Back"
                        send_image(phone, image, caption)
                        return "OK"
                except Exception as e:
                    print("Exception while fetching menu item:", str(e))
    
            if phone in booking_state and is_session_expired(booking_state[phone]['time']):
                booking_state.pop(phone)
                send_whatsapp_text(phone, "⏳ Session expired. Starting again.")
                send_main_menu(phone)
                return "OK"

            if msg.lower() in ['menu_option', 'Menu']:
                send_menu_list(phone)
                return "OK"

            elif msg in ['view_history', 'View History', 'view history']:
                history_booking(phone)
                return "OK"

            elif msg in ['book_table', 'Book Table']:
                booking_state[phone] = {"step": "name", "time": now}
                send_whatsapp_text(phone, "Enter your Name:")
                return "OK"

            elif phone in booking_state and booking_state[phone]["step"] == "date":
                entered_date = msg
                entered_name = booking_state[phone]["name"]
                booking_state[phone]['date'] = entered_date
                existing = check_booking(phone, entered_date)
                if existing:
                    booking_state[phone]['step'] = 'date'
                    booking_state[phone]['date'] = entered_date
                    booking_state[phone]['alerted_date'] = entered_date
                    send_booking_alert(phone)
                else:
                    booking_state[phone]['step'] = 'time'
                    send_whatsapp_text(phone, "Enter booking time (HH:MM):")
                    return "OK"
            
            elif msg == 'continue_booking':
                if phone in booking_state:
                    state = booking_state[phone]
                    state['time'] = now
                    state['step'] = 'date'
                    send_whatsapp_text(phone, "Enter booking date (YYYY-MM-DD):")
                else:
                    booking_state[phone] = {"step": "name", "time": now}
                    send_whatsapp_text(phone, "Enter your Name:")
                return "OK"

            elif msg == 'back_to_menu':
                booking_state.pop(phone, None)
                send_main_menu(phone)
                return "OK"
            elif msg == 'confirm_booking' and phone in booking_state and booking_state[phone]['step'] == 'confirm':
                state = booking_state[phone]
                confirm_booking(phone=phone, name=state['name'], date=state['date'], time_slot=state['time_slot'], people=state['people'], status='pending', txnid='N/A')
                payment_link = url_for('payment_success', phone=phone, _external=True)
                send_whatsapp_text(phone, f"✅ Booking received! To confirm, please pay here: {payment_link}")
                booking_state.pop(phone)
                return "OK"

            elif msg == 'cancel_booking_final':
                booking_state.pop(phone, None)
                send_whatsapp_text(phone, "❌ Booking cancelled.")
                send_main_menu(phone)
                return "OK"
                
            elif phone in booking_state:
                state = booking_state[phone]
                state['time'] = now
                if state['step'] == 'name':
                    if isValidName(msg):
                        state['name'] = msg
                        state['step'] = 'date'
                        send_whatsapp_text(phone, "Enter Date (YYYY-MM-DD):")
                    else:
                        send_whatsapp_text(phone, "Enter The Name In Alphabets Only")
                        state['step'] = 'name'
                        
                    return "OK"
                elif state['step'] == 'time':
                    if isValidTime(msg):
                        state['time_slot'] = msg
                        state['step'] = 'people'
                        send_whatsapp_text(phone, "Enter Number of People:")
                    else:
                        send_whatsapp_text(phone, "Enter the time in correct format HH:MM")
                    return "OK"

                elif state['step'] == 'people':
                    if isValidNumber(msg):
                        state['people'] = int(msg)
                        state['step'] = 'confirm'
                        send_whatsapp_confirmation(phone, state)
                    else:
                        send_whatsapp_text(phone, "Invalid input. Please enter the number of people as digits only.")
                    return "OK"

            else:
                send_main_menu(phone)
                return "OK"
            return "OK"

    except Exception as e:
        print("Error handling webhook:", str(e))
        return "Error", 500
# ===================== MAIN DATA VALIDATOR ENDS ====================
#
#      
# ===================== INPUT VALIDATOR =============================

def is_session_expired(state_time):
    return (datetime.datetime.now() - state_time).total_seconds() > SESSION_TIMEOUT_MINUTES * 60

def isValidDate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False
def isValidTime(time_text):
    try:
        datetime.datetime.strptime(time_text, '%H:%M')
        return True
    except ValueError:
        return False
def isValidNumber(number_text):
    return number_text.isdigit() and int(number_text) > 0
def isValidName(name_text):
    return bool(re.fullmatch(r'[A-Za-z\s]+', name_text.strip()))

# ===================== INPUT VALIDATOR ENDS ==================== 

# ===================== PAYMENT SETUP ===========================

@app.route('/book', methods=['POST'])
def book_table():
    data = request.form
    name = data.get('name')
    phone = data.get('phone')
    date = data.get('date')
    time = data.get('time')
    people = data.get('people')
    amount = 500

    txnid = str(uuid.uuid4())[:20]
    productinfo = "Table Booking"
    email = f"{phone}@payu.com"
    firstname = name
    hash_string = f"{MERCHANT_KEY}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{MERCHANT_SALT}"
    hashh = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()
    insert_booking(name, phone, date, time, people, 'pending', txnid)

    return render_template('payu_payment_form.html',
                           action_url=PAYU_BASE_URL,
                           key=MERCHANT_KEY,
                           txnid=txnid,
                           amount=amount,
                           productinfo=productinfo,
                           firstname=firstname,
                           email=email,
                           phone=phone,
                           surl=url_for('payment_success', _external=True),
                           furl=url_for('payment_failure', _external=True),
                           hashh=hashh)

@app.route('/payment-success', methods=['POST'])
def payment_success():
    txnid = request.form.get('txnid')
    status = request.form.get('status')
    received_hash = request.form.get('hash')

    key = MERCHANT_KEY
    salt = MERCHANT_SALT
    email = request.form.get('email')
    firstname = request.form.get('firstname')
    amount = request.form.get('amount')
    productinfo = request.form.get('productinfo')

    hash_sequence = f"{salt}|{status}|||||||||||{email}|{firstname}|{productinfo}|{amount}|{txnid}|{key}"
    calc_hash = hashlib.sha512(hash_sequence.encode('utf-8')).hexdigest().lower()

    if calc_hash != received_hash:
        return "Invalid hash – possible tampering", 400
    update_booking_status(txnid, 'paid')

    return "Payment Successful! Your table is booked."

@app.route('/payment-failure', methods=['POST'])
def payment_failure():
    txnid = request.form.get('txnid')
    update_booking_status(txnid, 'failed')
    return "Payment Failed. Please try again."

# =====================PAYMENT SETUP ENDS ========================
    
# ===================== ADMIN ROUTE =============================

@app.route('/admin')
def admin():
    bookings = booking_data()
    return render_template('admin.html', bookings=bookings)

@app.route('/send', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        phone = request.form['phone']
        message = request.form['message']
        send_whatsapp_text(phone, message)
        return f"✅ Message sent to {phone}!"
    return render_template('send.html')  

@app.route('/admin_data')
def admin_data():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Makes rows behave like dictionaries
    c = conn.cursor()
    c.execute("SELECT phone, name, date, time, people, status, txnid FROM bookings")
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route('/admin/menu')
def admin_menu(): 
    items = get_all()
    return render_template('menu_admin.html', items=items)

@app.route('/admin/menu/add', methods=['POST'])
def add_menu_item():
    title = request.form['title']
    description = request.form['description']
    price = int(request.form['price'])
    image = request.form['image']
    ingredients = request.form['ingredients']
    energy = request.form['energy']
    fat = request.form['fat']
    carbohydrates = request.form['carbohydrates']
    protein = request.form['protein']
    sodium = request.form['sodium']
    sugars = request.form['sugars']
    fiber = request.form['fiber']

    add_item(title, description, price, image, ingredients, energy, fat, carbohydrates, protein, sodium, sugars, fiber)
    return redirect(url_for('admin_menu'))

@app.route('/admin/menu/delete/<int:item_id>')
def delete_menu_item(item_id):
    delete_item(item_id)
    return redirect(url_for('admin_menu'))

# ===================== ADMIN ROUTE ENDS ==================== 
if __name__ == '__main__':
    app.run(debug=True)
