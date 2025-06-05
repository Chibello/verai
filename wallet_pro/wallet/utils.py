import uuid
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction

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
    balance_field = f"balance_{currency.lower()}"
    return getattr(user, balance_field, Decimal("0.00"))

def debit_user_balance(user, currency, amount):
    balance_field = f"balance_{currency.lower()}"
    current_balance = getattr(user, balance_field, None)
    if current_balance is None:
        logger.error(f"User {user} does not have balance field for {currency}")
        return False
    if current_balance < amount:
        logger.warning(f"User {user} insufficient funds: has {current_balance}, needs {amount}")
        return False
    setattr(user, balance_field, current_balance - amount)
    user.save(update_fields=[balance_field])
    logger.info(f"Debited {amount} {currency} from user {user}. New balance: {current_balance - amount}")
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

    reference = f"txn-{uuid.uuid4()}"

    try:
        with transaction.atomic():
            # Debit user balance first
            if not debit_user_balance(user, currency, total):
                return {
                    "status": "error",
                    "message": "Failed to debit user balance"
                }

            # Initiate Flutterwave transfer with the actual amount
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
                # Refund user balance on failure
                current_balance = get_user_balance(user, currency)
                balance_field = f"balance_{currency.lower()}"
                setattr(user, balance_field, current_balance + total)
                user.save(update_fields=[balance_field])

                logger.warning(f"Transfer failed, refunded {total} {currency} to user {user}. Reason: {flutterwave_response.get('message')}")
                return {
                    "status": "error",
                    "message": flutterwave_response.get("message", "Transfer failed"),
                    "flutterwave": flutterwave_response
                }
    except Exception as e:
        logger.error(f"Unexpected error during transfer: {str(e)}")
        return {
            "status": "error",
            "message": "Internal server error during transfer."
        }
