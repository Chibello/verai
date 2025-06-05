import uuid
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

# Default fallback fees in case dynamic ones aren't available
DEFAULT_FEES = {
    "NGN": Decimal("10.00"),
    "USD": Decimal("0.50"),
    "EUR": Decimal("0.45"),
    "GBP": Decimal("0.40"),
}

DEFAULT_VATS = {
    "NGN": Decimal("0.75"),
    "USD": Decimal("0.05"),
    "EUR": Decimal("0.045"),
    "GBP": Decimal("0.04"),
}


def get_user_balance(user, currency):
    field = f"balance_{currency.lower()}"
    return getattr(user, field, Decimal("0.00"))


def debit_user_balance(user, currency, amount):
    field = f"balance_{currency.lower()}"
    current_balance = getattr(user, field, None)
    if current_balance is None or current_balance < amount:
        logger.warning(f"User {user.username} has insufficient balance for {currency}")
        return False
    setattr(user, field, current_balance - amount)
    user.save(update_fields=[field])
    logger.info(f"Debited {amount} {currency} from {user.username}")
    return True


def credit_user_balance(user, currency, amount):
    field = f"balance_{currency.lower()}"
    current_balance = getattr(user, field, Decimal("0.00"))
    setattr(user, field, current_balance + amount)
    user.save(update_fields=[field])
    logger.info(f"Credited {amount} {currency} to {user.username}")


def calculate_fees(currency, amount):
    # Here you can add logic to fetch real-time fee from an API if available
    fee = DEFAULT_FEES.get(currency, Decimal("0.00"))
    vat = DEFAULT_VATS.get(currency, Decimal("0.00"))
    return fee, vat, amount + fee + vat


def initiate_flutterwave_transfer(amount, currency, bank_code, account_number, narration, reference):
    headers = {
        'Authorization': f'Bearer {settings.FLW_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {
        'account_bank': bank_code,
        'account_number': account_number,
        'amount': str(amount),
        'currency': currency,
        'narration': narration,
        'reference': reference,
        'callback_url': settings.FLUTTERWAVE_CALLBACK_URL,
        'debit_currency': currency,
    }

    try:
        response = requests.post("https://api.flutterwave.com/v3/transfers", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Flutterwave API error: {e}")
        return {"status": "error", "message": "Could not connect to Flutterwave"}


def create_transfer(user, currency, amount, bank_code, account_number, narration="Auto Transfer"):
    reference = f"txn-{uuid.uuid4()}"
    fee, vat, total = calculate_fees(currency, amount)

    balance = get_user_balance(user, currency)
    if balance < total:
        return {
            "status": "error",
            "message": "Insufficient funds",
            "required": str(total),
            "available": str(balance),
        }

    try:
        with transaction.atomic():
            if not debit_user_balance(user, currency, total):
                return {"status": "error", "message": "Balance deduction failed"}

            flutterwave_response = initiate_flutterwave_transfer(
                amount, currency, bank_code, account_number, narration, reference
            )

            if flutterwave_response.get("status") == "success":
                logger.info(f"Transfer {reference} successful for {user.username}")
                return {
                    "status": "success",
                    "message": "Transfer initiated",
                    "reference": reference,
                    "fee": str(fee),
                    "vat": str(vat),
                    "total_deducted": str(total),
                    "flutterwave": flutterwave_response,
                }
            else:
                # Refund on failure
                credit_user_balance(user, currency, total)
                logger.warning(f"Transfer failed. Refunded {total} to {user.username}")
                return {
                    "status": "error",
                    "message": flutterwave_response.get("message", "Transfer failed"),
                    "flutterwave": flutterwave_response,
                }

    except Exception as e:
        logger.exception(f"Transfer error for user {user.username}")
        return {
            "status": "error",
            "message": "Unexpected server error during transfer",
        }
