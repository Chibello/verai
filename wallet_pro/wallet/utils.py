import uuid
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from .models import Transaction

logger = logging.getLogger(__name__)

# === Fallback Fees ===
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

# === Fee Calculator ===
def calculate_fees(currency, amount):
    fee = DEFAULT_FEES.get(currency.upper(), Decimal("0.00"))
    vat = DEFAULT_VATS.get(currency.upper(), Decimal("0.00"))
    return fee, vat, amount + fee + vat

# === User Wallet Helpers ===
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
    logger.info(f"Refunded {amount} {currency} to {user.username}")

# === Flutterwave Wallet Balance Check ===
def get_flutterwave_wallet_balance(currency):
    url = f"https://api.flutterwave.com/v3/balances/{currency.upper()}"
    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}"
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("status") == "success":
            return Decimal(data["data"]["available_balance"])
        else:
            logger.warning(f"Failed to fetch Flutterwave balance: {data}")
            return Decimal("0.00")
    except Exception as e:
        logger.error(f"Error fetching FLW balance: {e}")
        return Decimal("0.00")

# === Initiate Transfer ===
def initiate_flutterwave_transfer(amount, currency, bank_code, account_number, narration, reference):
    url = "https://api.flutterwave.com/v3/transfers"
    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "account_bank": bank_code,
        "account_number": account_number,
        "amount": str(amount),
        "currency": currency,
        "narration": narration,
        "reference": reference,
        "callback_url": settings.FLUTTERWAVE_CALLBACK_URL,
        "debit_currency": currency,
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Flutterwave API error: {e}")
        return {"status": "error", "message": "Could not contact Flutterwave"}

# === Combined Transfer Logic ===
def process_user_payout(user, amount, currency, bank_code, account_number, narration="User Withdrawal"):
    reference = f"txn-{uuid.uuid4()}"
    fee, vat, total = calculate_fees(currency, amount)

    app_wallet_balance = get_user_balance(user, currency)
    if app_wallet_balance < total:
        return {"status": "error", "message": "Insufficient platform wallet balance"}

    flw_wallet_balance = get_flutterwave_wallet_balance(currency)
    if flw_wallet_balance < amount:
        return {"status": "error", "message": "Insufficient Flutterwave wallet balance"}

    try:
        with transaction.atomic():
            if not debit_user_balance(user, currency, total):
                return {"status": "error", "message": "Unable to debit user"}

            flutterwave_response = initiate_flutterwave_transfer(
                amount, currency, bank_code, account_number, narration, reference
            )

            if flutterwave_response.get("status") == "success":
                Transaction.objects.create(
                    user=user,
                    sender=user,
                    amount=amount,
                    currency=currency,
                    transaction_type='TRANSFER',
                    status='PENDING',
                    reference=reference,
                    narration=narration,
                    fee=fee,
                    vat=vat
                )
                return {"status": "success", "message": "Transfer initiated", "reference": reference}
            else:
                credit_user_balance(user, currency, total)
                return {
                    "status": "error",
                    "message": flutterwave_response.get("message", "Transfer failed"),
                    "flw_response": flutterwave_response
                }
    except Exception as e:
        logger.exception(f"Payout error for {user.username}")
        return {"status": "error", "message": "Unexpected server error during payout"}



'''
import uuid
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

#########
# wallet/utils.py
FEES = {
    "NGN": 10.00,
    "USD": 0.50,
    "EUR": 0.45,
    "GBP": 0.40
}

VATS = {
    "NGN": 0.75,
    "USD": 0.05,
    "EUR": 0.045,
    "GBP": 0.04
}

##########
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
'''
######################

import requests
from decimal import Decimal
from django.conf import settings
from .models import FlutterwaveWalletBalance

def update_flutterwave_wallet_balance():
    url = "https://api.flutterwave.com/v3/balances"

    headers = {
        "Authorization": f"Bearer {settings.FLW_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            balances = data.get("data", [])
            for wallet in balances:
                currency = wallet["currency"]
                amount = Decimal(wallet["available_balance"])

                obj, _ = FlutterwaveWalletBalance.objects.update_or_create(
                    currency=currency,
                    defaults={"balance": amount}
                )
        return True
    except Exception as e:
        print(f"[Balance Update Error] {e}")
        return False


######################
