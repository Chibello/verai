# services.py or utils.py

from django.core.exceptions import ValidationError

def withdraw_to_bank(user, amount):
    bank_details = getattr(user, 'bankdetails', None)
    if not bank_details:
        raise ValidationError("Bank details not found.")

    if user.wallet_balance < amount:
        raise ValidationError("Insufficient balance")

    # Deduct from wallet
    user.wallet_balance -= amount
    user.save()

    # ✅ Initiate external bank transfer (pseudo code)
    # e.g., flutterwave.transfer_funds(bank_details.account_number, bank_details.bank_code, amount)

    # You would handle:
    # - API request/response
    # - Logging
    # - Error handling
    # - Updating a withdrawal log or transaction history
