import uuid
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def initiate_flutterwave_transfer(amount, currency, account_bank, account_number, narration):
    reference = str(uuid.uuid4())
    headers = {
        'Authorization': f'Bearer {settings.FLW_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'account_bank': account_bank,
        'account_number': account_number,
        'amount': str(amount),
        'currency': currency,
        'narration': narration,
        'reference': reference,
        'callback_url': settings.FLUTTERWAVE_CALLBACK_URL,
        'debit_currency': currency
    }

    try:
        response = requests.post('https://api.flutterwave.com/v3/transfers', json=payload, headers=headers)
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Flutterwave request error: {str(e)}")
        return None
