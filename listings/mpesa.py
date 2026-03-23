# listings/mpesa.py
import requests
import base64
from requests.auth import HTTPBasicAuth
from datetime import datetime
from django.conf import settings


def format_phone(raw: str) -> str:
    raw = raw.strip().replace(" ", "").replace("-", "")
    if raw.startswith("0"):
        return "254" + raw[1:]
    if raw.startswith("+"):
        return raw[1:]
    return raw


def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r   = requests.get(url, auth=HTTPBasicAuth(
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET
    ))
    r.raise_for_status()
    return r.json()['access_token']


def initiate_stk_push(phone_number, amount):
    access_token = get_access_token()
    timestamp    = datetime.now().strftime('%Y%m%d%H%M%S')
    raw          = settings.MPESA_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    password     = base64.b64encode(raw.encode()).decode()

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password":          password,
        "Timestamp":         timestamp,
        "TransactionType":   "CustomerPayBillOnline",
        "Amount":            int(amount),
        "PartyA":            phone_number,
        "PartyB":            settings.MPESA_SHORTCODE,
        "PhoneNumber":       phone_number,
        "CallBackURL":       settings.MPESA_CALLBACK_URL,
        "AccountReference":  "ShambaShare",
        "TransactionDesc":   "Machinery Rental",
    }

    headers  = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers,
    )
    return response.json()