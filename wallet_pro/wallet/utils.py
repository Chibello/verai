
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
        logger.error(f"Error contacting Flutterwave API: {str(e)}")
        return None

def create_transfer(user, currency, amount, bank_code, account_number, narration="Auto Transfer"):
    from .models import Wallet

    try:
        wallet = Wallet.objects.get(user=user, currency=currency)
    except Wallet.DoesNotExist:
        return {"status": "error", "message": "Wallet not found"}

    fee = FEES.get(currency, Decimal("0.00"))
    vat = VATS.get(currency, Decimal("0.00"))
    total = amount + fee + vat

    if not wallet.debit(total):
        return {
            "status": "error",
            "message": "Insufficient funds",
            "required": str(total),
            "balance": str(wallet.balance)
        }

    reference = f"txn-{uuid.uuid4()}"
    payload = {
        "account_bank": bank_code,  # now using manually entered code
        "account_number": account_number,
        "amount": float(amount),
        "narration": narration,
        "currency": currency,
        "reference": reference,
        "callback_url": "https://verai.onrender.com/transfer/callback"
    }

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.flutterwave.com/v3/transfers", json=payload, headers=headers)
    result = response.json()

    if result.get("status") == "success":
        return {"status": "success", "message": "Transfer initiated", "payload": payload}
    else:
        return {"status": "error", "message": result.get("message", "Transfer failed"), "response": result}

