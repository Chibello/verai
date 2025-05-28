import uuid
from decimal import Decimal
from django.conf import settings
import stripe

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY  # Your Stripe Secret Key


def verify_account_name(account_number, bank_code):
    """Stripe doesn't directly provide account name verification. 
       Instead, you rely on KYC when onboarding users to Stripe Connect.
       This method is not applicable in Stripe. You need to ensure users have
       connected their accounts properly through Stripe Connect."""
    return None  # This functionality is different in Stripe.


def create_stripe_recipient(user, account_name, account_number, bank_code, currency='usd'):
    """Create a Stripe recipient (connected account)."""
    try:
        # Ensure the user has connected their Stripe account
        stripe_account_id = user.stripe_account_id  # Assuming the user's Stripe Account ID is saved in the model

        if not stripe_account_id:
            return None

        # Create a payout to the connected account (recipient)
        recipient = stripe.Account.create(
            type="custom",  # Type of account (custom for payout, express or standard for simpler onboarding)
            country="US",  # Update with the user's country or locale
            email=user.email  # Or another field to identify the account
        )

        return recipient.id  # Return the connected account's ID
    except stripe.error.StripeError as e:
        return None


def initiate_stripe_bank_transfer(user, amount, currency, account_bank, account_number, narration="Wallet payout"):
    """Initiate a Stripe payout to the connected bank account."""
    reference = str(uuid.uuid4())  # Generate a unique reference ID for the transaction
    currency = currency.lower()

    # Check user balance
    currency_field = f'balance_{currency}'
    if not hasattr(user, currency_field) or getattr(user, currency_field, Decimal('0')) < amount:
        return {
            'status': 'error',
            'message': 'Insufficient balance'
        }

    # Create connected account (recipient) for payout
    account_id = create_stripe_recipient(user, account_name=None, account_number=None, bank_code=None, currency=currency)
    if not account_id:
        return {
            'status': 'error',
            'message': 'Failed to create connected Stripe account'
        }

    # Initiate payout to the connected account
    try:
        payout = stripe.Payout.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            statement_descriptor=narration[:22],  # Max length of statement descriptor
            metadata={'user_id': user.id, 'narration': narration},
            stripe_account=account_id  # Send the payout to the connected account
        )

        # Deduct from the user's wallet balance
        currency_balance = getattr(user, currency_field)
        setattr(user, currency_field, currency_balance - amount)
        user.save()

        # Record transaction
        Transaction.objects.create(
            user=user,
            sender=user,
            amount=amount,
            currency=currency.upper(),
            transaction_type='TRANSFER',
            status='PENDING',  # Status is pending until webhook confirms the payout
            reference=payout.id,
            narration=narration
        )

        return {
            'status': 'success',
            'reference': payout.id,
            'message': 'Transfer initiated successfully',
            'data': payout
        }

    except stripe.error.StripeError as e:
        return {
            'status': 'error',
            'message': f'Stripe Error: {str(e)}'
        }
#########################

import stripe
from django.conf import settings

# Set up Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_onboarding_link(user):
    """Create a Stripe account link for user onboarding."""
    try:
        # Check if the user already has a connected Stripe account
        if user.stripe_account_id:
            return None  # User is already onboarded

        # Create a new connected account for the user (if not already done)
        account = stripe.Account.create(
            type="custom",  # Type of account (custom for payouts)
            country="US",  # Adjust to user's country
            email=user.email,
        )

        # Save the Stripe account ID to the user
        user.stripe_account_id = account.id
        user.save()

        # Create an account link to complete onboarding
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="https://yourdomain.com/reauth",  # URL to reattempt onboarding
            return_url="https://yourdomain.com/return",  # URL after successful onboarding
            type="account_onboarding",
        )

        return account_link.url  # URL to send to the user for onboarding
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return None
###################################################

def initiate_stripe_bank_transfer(user, amount, currency, narration="Wallet payout"):
    """Initiate a Stripe payout to the connected bank account."""
    reference = str(uuid.uuid4())  # Generate a unique reference ID for the transaction
    currency = currency.lower()

    # Check user balance
    currency_field = f'balance_{currency}'
    if not hasattr(user, currency_field) or getattr(user, currency_field, Decimal('0')) < amount:
        return {
            'status': 'error',
            'message': 'Insufficient balance'
        }

    # Check if the user has a connected Stripe account
    if not user.stripe_account_id:
        return {
            'status': 'error',
            'message': 'User has not connected their Stripe account'
        }

    # Initiate payout to the connected account
    try:
        payout = stripe.Payout.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            statement_descriptor=narration[:22],  # Max length of statement descriptor
            metadata={'user_id': user.id, 'narration': narration},
            stripe_account=user.stripe_account_id  # Send the payout to the connected account
        )

        # Deduct from the user's wallet balance
        currency_balance = getattr(user, currency_field)
        setattr(user, currency_field, currency_balance - amount)
        user.save()

        # Record transaction
        Transaction.objects.create(
            user=user,
            sender=user,
            amount=amount,
            currency=currency.upper(),
            transaction_type='TRANSFER',
            status='PENDING',  # Status is pending until webhook confirms the payout
            reference=payout.id,
            narration=narration
        )

        return {
            'status': 'success',
            'reference': payout.id,
            'message': 'Transfer initiated successfully',
            'data': payout
        }

    except stripe.error.StripeError as e:
        return {
            'status': 'error',
            'message': f'Stripe Error: {str(e)}'
        }
