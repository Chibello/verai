from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from wallet.models import User, Transaction

class CustomPaymentGateway:
    def __init__(self, user):
        self.user = user

    def validate_currency(self, currency):
        if self.user.currency != currency:
            raise ValidationError(f"Currency mismatch: wallet is {self.user.currency}, but received {currency}")

    def deposit(self, amount, currency):
        self.validate_currency(currency)
        amount = Decimal(amount)

        with transaction.atomic():
            self.user.wallet_balance += amount
            self.user.save()

            Transaction.objects.create(
                sender=self.user,
                receiver=self.user,
                amount=amount,
                transaction_type='Deposit',
                status='Completed',
                currency=currency
            )
        return f"Deposited {amount} {currency} successfully."

    def withdraw(self, amount, currency):
        self.validate_currency(currency)
        amount = Decimal(amount)

        if self.user.wallet_balance < amount:
            raise ValidationError("Insufficient funds for withdrawal.")

        with transaction.atomic():
            self.user.wallet_balance -= amount
            self.user.save()

            Transaction.objects.create(
                sender=self.user,
                receiver=self.user,
                amount=amount,
                transaction_type='Withdraw',
                status='Completed',
                currency=currency
            )
        return f"Withdrew {amount} {currency} successfully."

    def transfer(self, recipient_username, amount, currency):
        recipient = User.objects.get(username=recipient_username)
        amount = Decimal(amount)

        if self.user.currency != currency or recipient.currency != currency:
            raise ValidationError("Currency mismatch between sender and receiver.")

        if self.user.wallet_balance < amount:
            raise ValidationError("Insufficient funds for transfer.")

        with transaction.atomic():
            self.user.wallet_balance -= amount
            recipient.wallet_balance += amount
            self.user.save()
            recipient.save()

            Transaction.objects.create(
                sender=self.user,
                receiver=recipient,
                amount=amount,
                transaction_type='Transfer',
                status='Completed',
                currency=currency
            )
        return f"Transferred {amount} {currency} to {recipient_username} successfully."
