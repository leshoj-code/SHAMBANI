import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64

# Safaricom Sandbox Credentials
CONSUMER_KEY = 'GOfExMe7JDeN70G6Rswo2U08UdHkFCTa8jJGnNkAFCWk6UB7'
CONSUMER_SECRET = '30qL2jeMBSnNx0vJPm1DALfGCyUVCKB87vcEavQKT44UVUii8PmJyFFQSbrYjerz'
BUSINESS_SHORTCODE = '174379' # Sandbox default
LNM_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

def get_access_token():
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(api_url, auth=HTTPBasicAuth(CONSUMER_KEY, CONSUMER_SECRET))
    return r.json()['access_token']

def initiate_stk_push(phone_number, amount):
    access_token = get_access_token()
    api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((BUSINESS_SHORTCODE + LNM_PASSKEY + timestamp).encode()).decode()
    
    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number, # 2547XXXXXXXX
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://yourdomain.com/mpesa/callback", # Replace with your actual callback URL
        "AccountReference": "ShambaShare",
        "TransactionDesc": "Machinery Rental"
    }
    
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

from .mpesa import initiate_stk_push

def pay_for_machinery(request, pk):
    if request.method == "POST":
        equipment = get_object_or_404(Equipment, pk=pk)
        raw_phone = request.POST.get('phone')
        
        # Format phone to 2547XXXXXXXX
        formatted_phone = f"254{raw_phone}"
        amount = int(equipment.price_per_hour)
        
        # Trigger the STK Push
        response = initiate_stk_push(formatted_phone, amount)
        
        if response.get('ResponseCode') == '0':
            # SUCCESS: M-Pesa is processing
            equipment.is_rented = False 
            equipment.save()
            messages.success(request, "Check your phone! M-Pesa PIN prompt sent.")
        else:
            messages.error(request, "Error: " + response.get('CustomerMessage', 'Could not reach Safaricom'))
            
        return redirect('index')