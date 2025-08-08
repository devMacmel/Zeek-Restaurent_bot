import sqlite3, datetime
from zoneinfo import ZoneInfo
india_time = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
def get_db_connection():
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn
    
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY,
                    phone TEXT,
                    name TEXT,
                    date TEXT,
                    time TEXT,
                    people INTEGER,
                    status TEXT,
                    txnid TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS menu_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    price INTEGER,
                    image TEXT,
                    ingredients TEXT,
                    energy TEXT,
                    fat TEXT,
                    carbohydrates TEXT,
                    protein TEXT,
                    sodium TEXT,
                    sugars TEXT,
                    fiber TEXT
                )''')
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT 'pending'")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        c.execute("ALTER TABLE bookings ADD COLUMN txnid TEXT DEFAULT 'pending'")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def get_menu_items():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, description FROM menu_item")
    items = c.fetchall()
    conn.close()
    return items

def get_all():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM menu_item")
    items = c.fetchall()
    conn.close()
    return items

def booking_data():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bookings")
    data = c.fetchall()
    conn.close()
    return data

def add_item(title, description, price, image, ingredients, energy, fat, carbohydrates, protein, sodium, sugars, fiber):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO menu_item (title, description, price, image, ingredients, energy, fat, carbohydrates, protein, sodium, sugars, fiber) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              (title, description, price, image, ingredients, energy, fat, carbohydrates, protein, sodium, sugars, fiber))
    conn.commit()
    conn.close()

def delete_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM menu_item WHERE id=?', (item_id,))
    conn.commit()
    conn.close()

def confirm_booking(phone, name, date, time_slot, people, status='pending', txnid='N/A'):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings (phone, name, date, time, people, status, txnid)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (phone, name, date, time_slot, people, status, txnid))
    conn.commit()
    conn.close()

def check_booking(phone, entered_date):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE phone=? AND date=?", (phone, entered_date))
    existing = c.fetchone()
    conn.close()
    return existing

def history_booking(phone):
    from wa import send_whatsapp_text  # moved here
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE phone=?", (phone,))
    bookings = c.fetchall()
    text = "🗂️ *Your Bookings:*\n\n" + "\n\n".join([
        f"🧾 *Order ID:* {b[0]}\n👤 *Name:* {b[2]}\n📅 *Date:* {b[3]}\n⏰ *Time:* {b[4]}\n👥 *People:* {b[5]}\n💰 *Paid:* {b[6]}"
        for b in bookings
    ])
    send_whatsapp_text(phone, text)
    conn.close()

def item_data(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT title, price, image, ingredients, energy, fat, carbohydrates, protein, sodium, sugars, fiber FROM menu_item WHERE id=?", (item_id,))
    row = c.fetchone()
    conn.close()
    return row

def insert_booking(name, phone, date, time, people, status, txnid):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO bookings (phone, name, date, time, people, status, txnid) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (phone, name, date, time, people, status, txnid)
    )
    conn.commit()
    conn.close()

def update_booking_status(txnid, new_status):
    conn = get_db_connection()
    conn.execute("UPDATE bookings SET status = ? WHERE txnid = ?", (new_status, txnid))
    conn.commit()
    conn.close()



