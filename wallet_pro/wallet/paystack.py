import uuid
import requests
from decimal import Decimal
from django.conf import settings


PAYSTACK_BASE_URL = 'https://api.paystack.co'


def verify_account_name(account_number, bank_code):
    """Verify account name using Paystack resolve endpoint."""
    url = f'{PAYSTACK_BASE_URL}/bank/resolve'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    params = {
        'account_number': account_number,
        'bank_code': bank_code
    }

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    if result.get('status'):
        return result['data']['account_name']
    return None


def create_paystack_recipient(account_name, account_number, bank_code, currency='NGN'):
    """Create a transfer recipient on Paystack."""
    url = f'{PAYSTACK_BASE_URL}/transferrecipient'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "type": "nuban",
        "name": account_name,
        "account_number": account_number,
        "bank_code": bank_code,
        "currency": currency
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    if result.get('status') is True:
        return result['data']['recipient_code']
    return None


def initiate_paystack_bank_transfer(user, amount, currency, account_bank, account_number, narration="Wallet payout"):
    """Initiate a Paystack bank transfer after recipient creation and balance check."""
    reference = str(uuid.uuid4())
    currency = currency.upper()
    currency_field = f'balance_{currency.lower()}'

    # Check user balance
    if getattr(user, currency_field, Decimal('0')) < amount:
        return {
            'status': 'error',
            'message': 'Insufficient balance'
        }

def verify_account_name(account_number, bank_code):
    """Verify account name using Paystack resolve endpoint."""
    url = f'{PAYSTACK_BASE_URL}/bank/resolve'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    params = {
        'account_number': account_number,
        'bank_code': bank_code
    }

    response = requests.get(url, headers=headers, params=params)
    result = response.json()

    print("Paystack resolve response:", result)  # Debug line

    if result.get('status'):
        return result['data']['account_name']
    return None


    # Create transfer recipient
    recipient_code = create_paystack_recipient(account_name, account_number, account_bank, currency)
    if not recipient_code:
        return {
            'status': 'error',
            'message': 'Failed to create transfer recipient'
        }

    # Initiate transfer
    url = f'{PAYSTACK_BASE_URL}/transfer'
    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        "source": "balance",
        "amount": int(amount * 100),  # Convert to kobo
        "recipient": recipient_code,
        "reason": narration,
        "reference": reference
    }

    response = requests.post(url, json=payload, headers=headers)
    result = response.json()

    if result.get('status') is True:
        return {
            'status': 'success',
            'reference': reference,
            'message': result.get('message', 'Transfer initiated'),
            'data': result.get('data')
        }

    return {
        'status': 'error',
        'reference': reference,
        'message': result.get('message', 'Transfer failed'),
        'data': result.get('data')
    }
