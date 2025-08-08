import requests
from config import ACCESS_CODE, PHONE_ID
import json

def send_menu_list(phone):
    from db import get_menu_items 
    items = get_menu_items()
    rows = [
        {
            "id": str(item[0]),  # Use title as ID
            "title": item[1],
            "description": item[2]
        } for item in items
    ]

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍽️ Our Menu"},
            "body": {"text": "Select an item to see details:"},
            "footer": {"text": "Made with ❤️ by Zeek Restaurant"},
            "action": {
                "button": "View Menu",
                "sections": [{
                    "title": "Available Dishes",
                    "rows": rows
                }]
            }
        }
    }

    url = f'https://graph.facebook.com/v19.0/{PHONE_ID}/messages'
    headers = {'Authorization': f'Bearer {ACCESS_CODE}', 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("🔍 WhatsApp API Response:", response.status_code, response.text)

def send_whatsapp_text(phone, message):
    url = f'https://graph.facebook.com/v19.0/{PHONE_ID}/messages'
    headers = {
        'Authorization': f'Bearer {ACCESS_CODE}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("🔍 WhatsApp API Response:", response.status_code, response.text)  # PRINT THIS


def send_main_menu(phone):
    url = f'https://graph.facebook.com/v19.0/{PHONE_ID}/messages'
    headers = {'Authorization': f'Bearer {ACCESS_CODE}', 'Content-Type': 'application/json'}
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
            {"type": "reply", "reply": {"id": "view_history", "title": "View Bookings"}}
          ]
        }
      }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_booking_alert(phone):
    url = f'https://graph.facebook.com/v19.0/{PHONE_ID}/messages'
    headers = {'Authorization': f'Bearer {ACCESS_CODE}', 'Content-Type': 'application/json'}
    payload = {
      "messaging_product": "whatsapp",
      "to": phone,
      "type": "interactive",
      "interactive": {
        "type": "button",
        "body": {"text": "⚠️ You already have a booking today. Choose:"},
        "action": {
          "buttons": [
            {"type": "reply", "reply": {"id": "continue_booking", "title": "🆕 Continue"}},
            {"type": "reply", "reply": {"id": "back_to_menu", "title": "🔙 Back"}}
          ]
        }
      }
    }
    requests.post(url, headers=headers, data=json.dumps(payload))

def send_image(phone, image_url, caption):
    url = f'https://graph.facebook.com/v19.0/{PHONE_ID}/messages'
    headers = {
        'Authorization': f'Bearer {ACCESS_CODE}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    print("📤 send_image response:", response.status_code, response.text)

    if response.status_code != 200:
        print("❌ Error sending image. Sending fallback text instead.")
        send_whatsapp_text(phone, caption)

def send_whatsapp_confirmation(phone, state):
    summary = f"""Please confirm your booking:

👤 Name: {state['name']}
📅 Date: {state['date']}
⏰ Time: {state['time_slot']}
👥 People: {state['people']}
Click ✅ Confirm to proceed or ❌ Cancel to abort.
"""

    url = f'https://graph.facebook.com/v19.0/{PHONE_ID}/messages'
    headers = {
        'Authorization': f'Bearer {ACCESS_CODE}',
        'Content-Type': 'application/json'
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": summary},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "confirm_booking", "title": "✅ Confirm"}},
                    {"type": "reply", "reply": {"id": "cancel_booking_final", "title": "❌ Cancel"}}
                ]
            }
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    print("📤 Confirmation sent:", response.status_code, response.text)

