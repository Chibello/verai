import uuid
import requests
import logging
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

FEES = {
    "NGN": Decimal("10.00"),
    "USD": Decimal("0.50"),
    "EUR": Decimal("0.45"),
    "GBP": Decimal("0.40")
}

VATS = {
    "NGN": Decimal("0.75"),
    "USD": Decimal("0.05"),
    "EUR": Decimal("0.045"),
    "GBP": Decimal("0.04")
}

def get_user_balance(user, currency):
    # Customize this method based on your user model fields
    balance_field = f"balance_{currency.lower()}"
    return getattr(user, balance_field, Decimal("0.00"))

def debit_user_balance(user, currency, amount):
    balance_field = f"balance_{currency.lower()}"
    current_balance = getattr(user, balance_field, None)
    if current_balance is None:
        return False
    if current_balance < amount:
        return False
    setattr(user, balance_field, current_balance - amount)
    user.save(update_fields=[balance_field])
    return True

def initiate_flutterwave_transfer(amount, currency, account_bank, account_number, narration, reference):
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
        return {"status": "error", "message": "Failed to connect to Flutterwave."}

def create_transfer(user, currency, amount, bank_code, account_number, narration="Auto Transfer"):
    fee = FEES.get(currency, Decimal("0.00"))
    vat = VATS.get(currency, Decimal("0.00"))
    total = amount + fee + vat

    balance = get_user_balance(user, currency)
    if balance < total:
        return {
            "status": "error",
            "message": "Insufficient funds",
            "required": str(total),
            "available": str(balance)
        }

    # Debit user balance
    if not debit_user_balance(user, currency, total):
        return {
            "status": "error",
            "message": "Failed to debit user balance"
        }

    reference = f"txn-{uuid.uuid4()}"

    flutterwave_response = initiate_flutterwave_transfer(
        amount=amount,
        currency=currency,
        account_bank=bank_code,
        account_number=account_number,
        narration=narration,
        reference=reference
    )

    if flutterwave_response.get("status") == "success":
        return {
            "status": "success",
            "message": "Transfer initiated successfully",
            "reference": reference,
            "total_deducted": str(total),
            "fee": str(fee),
            "vat": str(vat),
            "flutterwave": flutterwave_response
        }
    else:
        # Refund balance on failure
        current_balance = get_user_balance(user, currency)
        balance_field = f"balance_{currency.lower()}"
        setattr(user, balance_field, current_balance + total)
        user.save(update_fields=[balance_field])

        return {
            "status": "error",
            "message": flutterwave_response.get("message", "Transfer failed"),
            "flutterwave": flutterwave_response
        }
