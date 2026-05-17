import requests
from django.conf import settings

def send_bill_whatsapp(customer, file_url):
    url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
    data = {
        "messaging_product": "whatsapp",
        "to": customer.whatsapp_number,  # must be in international format, e.g. "919876543210"
        "type": "document",
        "document": {
            "link": file_url,
            "caption": f"Milk Bill for {customer.name}"
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
