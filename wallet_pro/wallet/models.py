from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

### Custom User Model ###
class User(AbstractUser):
    wallet_balance = models.DecimalField(default=0, max_digits=15, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=[('USD', 'USD'), ('NGN', 'NGN'), ('EUR', 'EUR'), ('GBP', 'GBP')],
        default='NGN'
    )
    balance_usd = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    balance_ngn = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    balance_eur = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    balance_gbp = models.DecimalField(default=0, max_digits=12, decimal_places=2)

    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)  # Store Stripe account ID

    # Add related_name to avoid clash with other User models
    groups = models.ManyToManyField(
        Group,
        related_name='wallet_users',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='wallet_users',
        blank=True
    )

    def __str__(self):
        return self.username

### Transaction Model ###
class Transaction(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('NGN', 'Naira'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]

    TRANSACTION_TYPE_CHOICES = [
        ('TRANSFER', 'Transfer'),
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sent_transactions'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='received_transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    narration = models.TextField(blank=True, null=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} {self.currency} by {self.user.username}"

'''
# models.py
from django.db import models
from django.conf import settings

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('TRANSFER', 'Transfer'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=4)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    reference = models.CharField(max_length=100, unique=True)
    narration = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
'''
### Bank Details Model ###
class BankDetails(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet_bank_details'
    )
    account_number = models.CharField(max_length=20)
    bank_code = models.CharField(max_length=10)  # e.g., Flutterwave code
    bank_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

###############
class FlutterwaveWalletBalance(models.Model):
    currency = models.CharField(max_length=4, choices=[('NGN', 'NGN'), ('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR')])
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.currency} Wallet - {self.balance}"

